import bcrypt


from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from flask_restful import fields
from backend import db
from backend.models import Entity, Session


class User(db.Model, Entity):
  __tablename__ = 'users'

  marshaller = {'id_': fields.Integer, 'email_address': fields.String}

  email_address = Column(String, nullable=False, unique=True)

  password_hash = Column(String, nullable=False)
  password_salt = Column(String, nullable=False)

  surveys = relationship('Survey', back_populates='user')

  def set_password(self, password):
    salt_bytes = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)
    # Store as proper strings (like production), not byte representations
    self.password_salt = salt_bytes.decode('utf-8')
    self.password_hash = hash_bytes.decode('utf-8')

  def has_password(self, password):
    return self.password_hash.encode('utf-8') == bcrypt.hashpw(password.encode('utf-8'), self.password_salt.encode('utf-8'))

  def create_new_session(self):
    session = Session(user=self)
    return session
