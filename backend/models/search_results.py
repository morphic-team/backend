from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from flask_restful import fields
from backend import db
from backend.models import Entity


class SearchResult(db.Model, Entity):
  __tablename__ = 'search_results'
  marshaller = {
    'id_': fields.Integer,
    'next_id': fields.Integer,
    'previous_id': fields.Integer,
    'search_id': fields.Integer,
    'image_id': fields.Integer,
    'visible_link': fields.String,
    'direct_link': fields.String,
    'completion_state': fields.String,
    'duplicate_of_id': fields.Integer,
    'image_scraped_state': fields.String,
  }
  
  # Marshaller with duplicate pool for detail views
  detail_marshaller = {
    'id_': fields.Integer,
    'next_id': fields.Integer,
    'previous_id': fields.Integer,
    'search_id': fields.Integer,
    'image_id': fields.Integer,
    'visible_link': fields.String,
    'direct_link': fields.String,
    'completion_state': fields.String,
    'duplicate_of_id': fields.Integer,
    'image_scraped_state': fields.String,
    'duplicate_pool': fields.List(fields.Nested({
      'id_': fields.Integer,
      'visible_link': fields.String,
      'direct_link': fields.String,
      'completion_state': fields.String,
      'image_scraped_state': fields.String,
      'duplicate_of_id': fields.Integer,
    })),
  }

  search_id = Column(Integer, ForeignKey('searches.id_'), nullable=False)
  search = relationship('Search', back_populates='results')

  visible_link = Column(String, nullable=False)
  direct_link = Column(String, nullable=False)

  class ImageScrapedStates:
    NEW = 'NEW'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

  image_scraped_state = Column(String, default='NEW', nullable=False)
  image_id = Column(Integer, ForeignKey('images.id_'), nullable=True)
  image = relationship('Image')

  class CompletionStates:
    NOT_USABLE = 'NOT_USABLE'
    REVISIT = 'REVISIT'
    DONE = 'DONE'

  completion_state = Column(String, default=CompletionStates.REVISIT, nullable=False)

  # Duplicate tracking - points to the canonical SearchResult this is a duplicate of
  duplicate_of_id = Column(Integer, ForeignKey('search_results.id_'), nullable=True)
  duplicate_of = relationship('SearchResult', remote_side='SearchResult.id_', backref='duplicates')


  result_fields = relationship('ResultField', back_populates='search_result')

  @property
  def next_id(self):
    return (
        SearchResult
        .query
        .filter(SearchResult.search==self.search)
        .filter(SearchResult.id_>self.id_)
        .order_by(SearchResult.id_)
        .first()
        .id_
    )

  @property
  def previous_id(self):
    return (
        SearchResult
        .query
        .filter(SearchResult.search==self.search)
        .filter(SearchResult.id_<self.id_)
        .order_by(SearchResult.id_.desc())
        .first()
        .id_
    )

