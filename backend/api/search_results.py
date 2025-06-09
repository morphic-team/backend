import json
import io
import time
import hmac
import hashlib
import os
from flask import Blueprint, send_file, abort, request, g
from flask_restful import marshal_with, fields, reqparse, marshal
from backend import db
from backend.models import SearchResult, ResultField, SurveyField, Search, Image, Session, User
from backend.api.utils import my_jsonify
from backend.auth import require_auth

search_results_bp = Blueprint('search_results', __name__)

SERVER_SECRET = os.environ['MORPHIC_IMAGE_SIGNING_SECRET']


def generate_signed_image_url(user_id, search_result_id, endpoint):
  """Generate a signed URL for accessing cached images or thumbnails"""
  expires = int(time.time() + 3600)  # 1 hour expiry
  
  # Derive a signing key unique to this user (no storage needed)
  user_signing_key = hmac.new(
    SERVER_SECRET.encode(), 
    f"image_access_{user_id}".encode(), 
    hashlib.sha256
  ).digest()
  
  # Sign the specific request
  payload = f"{search_result_id}:{expires}"
  signature = hmac.new(user_signing_key, payload.encode(), hashlib.sha256).hexdigest()
  
  return f"/api/search_results/{search_result_id}/{endpoint}?u={user_id}&e={expires}&s={signature}"


def verify_image_access(search_result_id):
  """Verify that the user has valid access to this image"""
  user_id = request.args.get('u')
  expires = request.args.get('e')
  signature = request.args.get('s')
  
  if not user_id or not expires or not signature:
    abort(403)
  
  try:
    expires_int = int(expires)
  except ValueError:
    abort(403)
  
  # Check expiration
  if expires_int < time.time():
    abort(410)  # Expired
  
  # Re-derive the same signing key for this user
  user_signing_key = hmac.new(
    SERVER_SECRET.encode(), 
    f"image_access_{user_id}".encode(), 
    hashlib.sha256
  ).digest()
  
  # Verify signature
  expected_payload = f"{search_result_id}:{expires}"
  expected_sig = hmac.new(user_signing_key, expected_payload.encode(), hashlib.sha256).hexdigest()
  if not hmac.compare_digest(signature, expected_sig):
    abort(403)
  
  # Verify user still has survey access
  search_result = SearchResult.query.filter(SearchResult.id_==search_result_id).first()
  if not search_result:
    abort(404)
  
  # Check if user owns the survey this search result belongs to
  if search_result.search.survey.user_id != int(user_id):
    abort(403)
  
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
