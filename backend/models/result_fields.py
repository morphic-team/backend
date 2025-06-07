from flask_restful import fields
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from backend import db
from backend.models import Entity


class ResultField(db.Model, Entity):
  __tablename__ = 'result_fields'
  
  # NOTE: This model has a "diamond dependency" issue where result_fields
  # could theoretically reference SearchResult and SurveyField from different surveys.
  # See docs/DATA_MODEL.md for details. No database constraint is currently feasible.
  # Solution: Be careful in application logic when creating ResultFields.
  
  marshaller = {
    'search_result_id': fields.Integer,
    'survey_field_id': fields.Integer,
    'value': fields.String,
  }
  search_result_id = Column(Integer, ForeignKey('search_results.id_'), nullable=False)
  search_result = relationship('SearchResult', back_populates='result_fields')

  survey_field_id = Column(Integer, ForeignKey('survey_fields.id_'), nullable=False)
  survey_field = relationship('SurveyField', back_populates='result_fields')

  value = Column(String, nullable=False)
