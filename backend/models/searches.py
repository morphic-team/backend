from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_restful import fields
from backend import db
from backend.models import Entity


class Search(db.Model, Entity):
  __tablename__ = 'searches'
  marshaller = {
    'id_': fields.Integer,
    'name': fields.String,
    'comments': fields.String,
    'search_query': fields.String,
    'are_results_uploaded': fields.Boolean,
  }

  are_results_uploaded = Column(Boolean, default=False, nullable=False)

  survey_id = Column(Integer, ForeignKey('surveys.id_'), nullable=False)
  survey = relationship('Survey', back_populates='searches')

  results = relationship('SearchResult', back_populates='search')

  name = Column(String, nullable=False)

  search_query = Column(String, nullable=False)

  comments = Column(String)
