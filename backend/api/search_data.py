from flask import abort, Blueprint, request
from flask_restful import reqparse
from flask_cors import cross_origin
from backend import db
from backend.models import User, Search, SearchResult, Image
from backend.auth import require_auth
from backend.url_signing import verify_signed_url
from backend.search_urls import verify_upload_google_results_signature
import json
import hashlib

search_data_bp = Blueprint('search_data', __name__)


@search_data_bp.route('/upload-google-results', methods=['POST', 'OPTIONS'])
@cross_origin(origins='chrome-extension://*', supports_credentials=False, allow_headers=['Content-Type', 'X-Upload-Token'])
def upload_search_data():
  # Handle preflight OPTIONS request
  if request.method == 'OPTIONS':
    return '', 200
  
  parser = reqparse.RequestParser()
  parser.add_argument('morphic_id', type=int)
  parser.add_argument('results')
  args = parser.parse_args()

  search_id = args.morphic_id
  if not search_id:
    abort(400)

  # Verify the upload signature token from header
  token = request.headers.get('X-Upload-Token')
  if not token:
    abort(400, "Missing upload token")
    
  try:
    payload = verify_upload_google_results_signature(token)
    user_id = payload['user_id']
    expected_search_id = payload['search_id']
    limit = payload['limit']
    
    if search_id != expected_search_id:
      abort(403, "Search ID mismatch")
  except Exception:
    abort(403, "Invalid upload token")
  
  # Get the search (we know it exists from the authorization check)
  search = Search.query.filter(Search.id_==search_id).first()

  for result in json.loads(args.results):
    search_result = SearchResult(
      direct_link=result['image_link'],
      visible_link=result['visible_link'],
      search=search,
      image_scraped_state=SearchResult.ImageScrapedStates.NEW
    )
    db.session.add(search_result)

  search.are_results_uploaded = True

  db.session.add(search)
  db.session.commit()

  return 'OK', 200
