import json
import io
from flask import Blueprint, send_file, abort, g
from flask_restful import marshal_with, fields, reqparse, marshal
from backend import db
from backend.models import SearchResult, ResultField, SurveyField, Search, Image, Session, User
from backend.api.utils import my_jsonify
from backend.auth import require_auth
from backend.url_signing import generate_signed_url, verify_signed_url

search_results_bp = Blueprint('search_results', __name__)


def generate_signed_image_url(user_id, search_result_id, endpoint):
  """Generate a signed URL for accessing cached images or thumbnails"""
  return generate_signed_url(
    user_id, 
    search_result_id, 
    f"/api/search_results/{search_result_id}/{endpoint}",
    "image_access"
  )


def verify_image_access(search_result_id):
  """Verify that the user has valid access to this image"""
  def check_image_authorization(user_id, search_result_id):
    """Check if user owns the survey this search result belongs to"""
    search_result = SearchResult.query.filter(SearchResult.id_==search_result_id).first()
    if not search_result:
      abort(404)
    return search_result.search.survey.user_id == user_id
  
  user_id = verify_signed_url(search_result_id, "image_access", check_image_authorization)
  
  # Return the search result for the endpoint to use
  search_result = SearchResult.query.filter(SearchResult.id_==search_result_id).first()
  return search_result


def build_detailed_search_result_response(search_result, current_user=None):
  """Build detailed search result response with field values, search info, and duplicate pool"""
  marshaller = SearchResult.detail_marshaller.copy()

  field_values = {}
  field_values_marshaller = {}
  for result_field in search_result.result_fields:
    field_id = str(result_field.survey_field.id_)
    field_values[field_id] = result_field.value
    field_values_marshaller[field_id] = fields.String

  marshaller['field_values'] = fields.Nested(field_values_marshaller)
  marshaller['search'] = fields.Nested(Search.marshaller)

  # Add signed image URLs if user is authenticated and image is cached
  if current_user and search_result.image_scraped_state == 'SUCCESS':
    marshaller['cached_image_url'] = fields.String
    marshaller['cached_thumbnail_url'] = fields.String
    search_result.cached_image_url = generate_signed_image_url(current_user.id_, search_result.id_, 'image')
    search_result.cached_thumbnail_url = generate_signed_image_url(current_user.id_, search_result.id_, 'thumbnail')

  # Get all results in the same duplicate pool (always including self)
  if search_result.duplicate_of_id:
    # This is a duplicate - get canonical + all duplicates of same canonical
    canonical = SearchResult.query.get(search_result.duplicate_of_id)
    duplicates = SearchResult.query.filter(SearchResult.duplicate_of_id == search_result.duplicate_of_id).all()
    search_result.duplicate_pool = [canonical] + duplicates
  else:
    # This is canonical - get self + all duplicates pointing to it
    duplicates = SearchResult.query.filter(SearchResult.duplicate_of_id == search_result.id_).all()
    search_result.duplicate_pool = [search_result] + duplicates

  search_result.field_values = field_values
  return marshal(search_result, marshaller)


@search_results_bp.route('/search_results/<int:search_result_id>')
@require_auth
@my_jsonify
def get_search_result(search_result_id):
  search_result = SearchResult.query.filter(SearchResult.id_==search_result_id).first()
  return build_detailed_search_result_response(search_result, g.current_user)

@search_results_bp.route('/search_results/<int:search_result_id>', methods=['PATCH'])
@require_auth
@my_jsonify
def update_search_result(search_result_id):
  parser = reqparse.RequestParser()
  parser.add_argument('completion_state', type=str)
  parser.add_argument('field_values', location='json', type=dict, default={})
  args = parser.parse_args()

  search_result = SearchResult.query.filter(SearchResult.id_==search_result_id).first()
  search_result.completion_state = args.completion_state
  survey = search_result.search.survey

  for field_id, field_value in args.field_values.items():
    survey_field = (SurveyField.query
      .filter(SurveyField.id_==int(field_id))
      .filter(SurveyField.survey==survey)
      .first()
    )
    if not survey_field:
      return {'error': f'Survey field not found: {field_id}'}, 400
      
    result_field = (ResultField.query
      .filter(ResultField.search_result==search_result)
      .filter(ResultField.survey_field==survey_field)
      .first()
    )
    
    # Handle null/empty values by deleting the result field
    if field_value is None or field_value == '':
      if result_field is not None:
        db.session.delete(result_field)
      continue
      
    # Handle non-null values by creating or updating the result field
    if result_field is None:
      result_field = ResultField(
        search_result=search_result,
        survey_field=survey_field,
      )
    # Serialize dict values (like location data) to JSON strings
    if isinstance(field_value, dict):
      result_field.value = json.dumps(field_value)
    else:
      result_field.value = field_value

    db.session.add(result_field)

  db.session.add(search_result)
  db.session.commit()

  return build_detailed_search_result_response(search_result, g.current_user)


@search_results_bp.route('/search_results/<int:search_result_id>/image', methods=['GET'])
def serve_cached_image(search_result_id):
  """Serve the cached full image for a search result with signed URL authentication"""
  # Verify access and get search result
  search_result = verify_image_access(search_result_id)
  
  if not search_result.image or not search_result.image.image_file:
    abort(404)
  
  # Create a BytesIO object from the binary data
  image_data = io.BytesIO(search_result.image.image_file)
  image_data.seek(0)
  
  return send_file(
    image_data,
    mimetype='image/jpeg',
    as_attachment=False,
    download_name=f'search_result_{search_result_id}.jpg'
  )


@search_results_bp.route('/search_results/<int:search_result_id>/thumbnail', methods=['GET'])
def serve_cached_thumbnail(search_result_id):
  """Serve the cached thumbnail for a search result with signed URL authentication"""
  # Verify access and get search result
  search_result = verify_image_access(search_result_id)
  
  if not search_result.image or not search_result.image.thumbnail_file:
    abort(404)
  
  # Create a BytesIO object from the binary data
  thumbnail_data = io.BytesIO(search_result.image.thumbnail_file)
  thumbnail_data.seek(0)
  
  return send_file(
    thumbnail_data,
    mimetype='image/jpeg',
    as_attachment=False,
    download_name=f'search_result_{search_result_id}_thumb.jpg'
  )
