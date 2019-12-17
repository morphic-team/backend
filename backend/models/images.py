from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from backend import db
from backend.models import Entity


class Image(db.Model, Entity):
  __tablename__ = 'images'

  image_file = Column(LargeBinary, nullable=False)
  thumbnail_file = Column(LargeBinary, nullable=False)
  image_hash = Column(String, nullable=False)
