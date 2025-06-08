from flask_restful import fields
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend import db
from backend.models import Entity


class SurveyField(db.Model, Entity):
  __tablename__ = 'survey_fields'
  marshaller = {
    'id_': fields.Integer,
    'label': fields.String,
    'field_type': fields.String,
    'options': fields.List(fields.String),
    'order': fields.Integer,
  }

  survey_id = Column(Integer, ForeignKey('surveys.id_'), nullable=False)
  survey = relationship('Survey', back_populates='fields')

  label = Column(String)
  field_type = Column(String)
  options = Column(String)
  order = Column(Integer, nullable=False)

  result_fields = relationship('ResultField', back_populates='survey_field')
