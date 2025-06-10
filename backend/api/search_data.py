from flask import abort, Blueprint
from flask_restful import reqparse
from flask_cors import cross_origin
from backend import db
from backend.models import User, Search, SearchResult
from backend.auth import require_auth
import json

search_data_bp = Blueprint('search_data', __name__)


@search_data_bp.route('/upload-google-results', methods=['POST', 'OPTIONS'])
@cross_origin(origins='chrome-extension://*', supports_credentials=True, allow_headers=['Content-Type', 'X-Session-Token'])
@require_auth
def upload_search_data():
  parser = reqparse.RequestParser()
  parser.add_argument('morphic_id', type=int)
  parser.add_argument('results')
  args = parser.parse_args()

  search = Search.query.filter(Search.id_==args.morphic_id).first()

  if search is None:
    abort(404)

  for result in json.loads(args.results):
    search_result = SearchResult(
      direct_link=result['image_link'],
      visible_link=result['visible_link'],
      search=search,
    )
    db.session.add(search_result)

  search.are_results_uploaded = True

  db.session.add(search)
  db.session.commit()

  return 'OK', 200
