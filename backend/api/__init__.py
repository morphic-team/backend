from flask import Blueprint


api = Blueprint('api', __name__)

import backend.api.sessions
import backend.api.users
import backend.api.surveys
import backend.api.search_data
import backend.api.search_results
import backend.api.searches
