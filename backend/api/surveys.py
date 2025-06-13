import json
import unicodecsv
from datetime import datetime
from flask import send_file, Blueprint, request, g
from flask_restful import marshal_with, reqparse, fields
from sqlalchemy.orm import joinedload
from backend import db
from backend.models import Survey, SearchResult, Search, SurveyField, ResultField
from backend.api.utils import my_jsonify, paginate_marshaller
from backend.auth import require_auth
from io import BytesIO

surveys_bp = Blueprint('surveys', __name__)

def normalize_field_name(label):
  """Normalize field labels for CSV headers by replacing problematic characters"""
  import re
  # Remove or replace problematic characters
  normalized = re.sub(r'[^\w\s-]', '', label)  # Remove non-alphanumeric except spaces and hyphens
  normalized = re.sub(r'\s+', '_', normalized)  # Replace spaces with underscores
  normalized = normalized.lower().strip('_')  # Lowercase and trim underscores
  return normalized

@surveys_bp.route('/surveys/<int:survey_id>/export-results')
@require_auth
def get_survey_results(survey_id):
  # Get survey with fields
  survey = (
    Survey
    .query
    .filter(Survey.id_ == survey_id)
    .options(joinedload(Survey.fields))
    .first()
  )
  
  if not survey:
    return {'error': 'Survey not found'}, 404

  # Get all search results for this survey using proper joins
  search_results = (
    SearchResult
    .query
    .join(Search)
    .filter(Search.survey_id == survey_id)
    .options(joinedload(SearchResult.result_fields))
    .options(joinedload(SearchResult.search))
    .order_by(SearchResult.id_.desc())
    .all()
  )

  field_names = ['morphic_id', 'completion_state']
  for field in survey.fields:
      label = field.label
      if field.field_type == 'location':
          label += " (lat, lon)"
      field_names.append(normalize_field_name(label))
  field_names += ['search_name', 'search_query', 'visible_link', 'direct_link']

  f = BytesIO()

  writer = unicodecsv.DictWriter(f, field_names, encoding='utf-8')
  writer.writeheader()

  for search_result in search_results:
    d = {
        'morphic_id': search_result.id_,
        'completion_state': search_result.completion_state,
        'search_name': search_result.search.name,
        'search_query': search_result.search.search_query,
        'visible_link': search_result.visible_link,
        'direct_link': search_result.direct_link,
    }
    for result_field in sorted(search_result.result_fields, key=lambda rf: rf.id_):
      label = result_field.survey_field.label or ''
      value = result_field.value or ''
      if result_field.survey_field.field_type == 'location':
          location_dict = json.loads(value)
          value = '%s, %s' % (location_dict['latitude'], location_dict['longitude'])
          label += " (lat, lon)"

      d[normalize_field_name(label)] = value
    writer.writerow(d)

  f.seek(0)

  return send_file(f, mimetype='text/csv')


@surveys_bp.route('/surveys/<int:survey_id>')
@require_auth
@my_jsonify
def get_survey(survey_id):
  # joined load onto survey, search, survey_fields and search_results and survey_result_fields.
  survey = Survey.query.filter(Survey.id_==survey_id).first()
  
  if not survey:
    return {'error': 'Survey not found'}, 404
  
  # Build response manually to handle JSON options field properly
  result = {
    'id_': survey.id_,
    'name': survey.name,
    'comments': survey.comments,
    'fields': []
  }
  
  for field in survey.fields:
    field_data = {
      'id_': field.id_,
      'label': field.label,
      'field_type': field.field_type,
      'order': field.order,
      'options': json.loads(field.options) if field.options else []
    }
    result['fields'].append(field_data)
  
  return result

@surveys_bp.route('/surveys/<int:survey_id>/search_results')
@require_auth
@my_jsonify
@marshal_with(paginate_marshaller(SearchResult.marshaller))
def get_surveys_search_results(survey_id):
  # Parse query parameters
  completion_state = request.args.get('completion_state', None)
  per_page = int(request.args.get('per_page', 60))
  page = int(request.args.get('page', 1))

  offset = per_page * page - per_page

  search_results_query = (SearchResult.query
    .join(Search)
    .filter(Search.survey_id==survey_id)
    .order_by(SearchResult.id_)
  )
  
  # Filter by completion state if provided
  if completion_state:
    search_results_query = search_results_query.filter(SearchResult.completion_state==completion_state)

  return {
    'count': search_results_query.count(),
    'results': (search_results_query
      .limit(per_page)
      .offset(offset)
      .all()
    ),
    'offset': offset,
    'limit': per_page,
  }

@surveys_bp.route('/surveys/<int:survey_id>/searches')
@require_auth
@my_jsonify
@marshal_with(paginate_marshaller(Search.marshaller))
def get_surveys_searches(survey_id):
  searches = (Search.query
    .filter(Search.survey_id==survey_id)
    .all())
  return {
    'results': searches
  }


@surveys_bp.route('/surveys/<int:survey_id>/searches', methods=['POST'])
@require_auth
@my_jsonify
@marshal_with(Search.marshaller)
def create_search(survey_id):
  parser = reqparse.RequestParser()
  parser.add_argument('name', str)
  parser.add_argument('comments', str)
  parser.add_argument('search_query', str)
  args = parser.parse_args()
  search = Search(
    survey_id=survey_id,
    name=args.name,
    comments=args.comments,
    search_query=args.search_query,
  )
  db.session.add(search)
  db.session.commit()
  return search


@surveys_bp.route('/surveys/<int:survey_id>', methods=['PATCH'])
@require_auth
@my_jsonify
def update_survey(survey_id):
  survey = Survey.query.filter(Survey.id_ == survey_id).first()
  
  if not survey:
    return {'error': 'Survey not found'}, 404
  
  parser = reqparse.RequestParser()
  parser.add_argument('is_archived', type=bool)
  args = parser.parse_args()
  
  # Handle archive status update
  if args.is_archived is not None:
    if args.is_archived and not survey.is_archived:
      # Archiving the survey
      survey.is_archived = True
      survey.archived_at = datetime.utcnow()
    elif not args.is_archived and survey.is_archived:
      # Unarchiving the survey
      survey.is_archived = False
      survey.archived_at = None
    # If status isn't changing, no need to update timestamps
  
  db.session.commit()
  
  return {
    'id_': survey.id_,
    'name': survey.name,
    'comments': survey.comments,
    'is_archived': survey.is_archived,
    'archived_at': survey.archived_at.isoformat() if survey.archived_at else None
  }
