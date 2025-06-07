from backend.models import Search
from flask import Blueprint
from flask_restful import marshal_with
from backend.api.utils import my_jsonify

searches_bp = Blueprint('searches', __name__)


@searches_bp.route('/searches/<int:search_id>')
@my_jsonify
@marshal_with(Search.marshaller)
def get_search(search_id):
  search = Search.query.filter(Search.id_ == search_id).first()
  return search
