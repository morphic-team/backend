from sqlalchemy import Column, Integer
from backend import db


class Entity(object):
  id_ = Column(Integer, primary_key=True)

from backend.models.sessions import Session
from backend.models.users import User
from backend.models.surveys import Survey
from backend.models.survey_fields import SurveyField
from backend.models.searches import Search
from backend.models.images import Image
from backend.models.search_results import SearchResult
from backend.models.result_fields import ResultField
