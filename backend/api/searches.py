from backend.models import Search
from flask import Blueprint, g
from flask_restful import marshal_with, reqparse
from backend.api.utils import my_jsonify
from backend.auth import require_auth
from backend.search_urls import generate_upload_google_results_url, generate_google_search_url

# Token expiration time in seconds (24 hours)
UPLOAD_TOKEN_EXPIRES_IN = 24 * 3600

searches_bp = Blueprint('searches', __name__)


@searches_bp.route('/searches/<int:search_id>')
@require_auth
@my_jsonify
@marshal_with(Search.marshaller)
def get_search(search_id):
  search = Search.query.filter(Search.id_ == search_id).first()
  return search


@searches_bp.route('/searches/<int:search_id>/generate-upload-url', methods=['POST'])
@require_auth
@my_jsonify
def generate_search_upload_url(search_id):
  parser = reqparse.RequestParser()
  parser.add_argument('limit', type=int, required=True)
  args = parser.parse_args()
  
  # Verify user owns this search
  search = Search.query.filter(Search.id_ == search_id).first()
  if not search:
    return {'error': 'Search not found'}, 404
    
  if search.survey.user_id != g.current_user.id_:
    return {'error': 'Access denied'}, 403
  
  # Generate upload token
  upload_token = generate_upload_google_results_url(
    g.current_user.id_,
    search_id,
    args.limit,
    expires_in=UPLOAD_TOKEN_EXPIRES_IN
  )
  
  # Generate Google search URL with embedded token
  google_search_url = generate_google_search_url(search.search_query, upload_token)
  
  return {
    'google_search_url': google_search_url,
    'limit': args.limit,
    'expires_in': UPLOAD_TOKEN_EXPIRES_IN
  }
