from flask_restful import fields
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend import db
from backend.models import Entity


class Survey(db.Model, Entity):
  __tablename__ = 'surveys'

  marshaller = {
    'id_': fields.Integer,
    'name': fields.String,
    'comments': fields.String,
  }

  name = Column(String, nullable=False)
  comments = Column(String)

  user_id = Column(Integer, ForeignKey('users.id_'), nullable=False)
  user = relationship('User', back_populates='surveys')

  searches = relationship('Search', back_populates='survey')
  fields = relationship('SurveyField', back_populates='survey')
