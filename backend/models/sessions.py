import secrets
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from flask_restful import fields
from backend import db
from backend.models import Entity


class Session(db.Model, Entity):
  __tablename__ = 'sessions'
  marshaller = {'id_': fields.Integer, 'token': fields.String}

  user_id = Column(Integer, ForeignKey('users.id_'), nullable=False)
  token = Column(String, unique=True, nullable=False)
  user = relationship('User')
  
  def __init__(self, user):
    self.user = user
    self.token = secrets.token_urlsafe(32)  # 256-bit secure random token
