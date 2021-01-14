from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from flask.ext.restful import fields
from backend import db
from backend.models import Entity, Tag


class SearchResult(db.Model, Entity):
  __tablename__ = 'search_results'
  marshaller = {
    'id_': fields.Integer,
    'next_id': fields.Integer,
    'previous_id': fields.Integer,
    'user_id': fields.Integer,
    'search_id': fields.Integer,
    'image_id': fields.Integer,
    'visible_link': fields.String,
    'direct_link': fields.String,
    'completion_state': fields.String,
  }

  search_id = Column(Integer, ForeignKey('searches.id_'), nullable=False)
  search = relationship('Search')

  visible_link = Column(String, nullable=False)
  direct_link = Column(String, nullable=False)

  class ImageScrapedStates:
    NEW = 'NEW'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

  image_scraped_state = Column(String, default='NEW', nullable=False)
  image_id = Column(Integer, ForeignKey('images.id_'), nullable=False)
  image = relationship('Image')

  class CompletionStates:
    NOT_USABLE = 'NOT_USABLE'
    REVISIT = 'REVISIT'
    DONE = 'DONE'

  completion_state = Column(String, default=CompletionStates.REVISIT, nullable=False)

  tags = relationship('Tag')

  result_fields = relationship('ResultField')

  @property
  def next_id(self):
    return (
        SearchResult
        .query
        .filter(SearchResult.search==self.search)
        .filter(SearchResult.user==self.user)
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
        .filter(SearchResult.user==self.user)
        .filter(SearchResult.id_<self.id_)
        .order_by(SearchResult.id_.desc())
        .first()
        .id_
    )

  def update_tags(self):
    new_tags = []

    new_tags.append(Tag(
      search_result=self,
      value='%s: %s' % ('completion_state', self.completion_state)
    ))

    for result_field in self.result_fields:
      new_tags.append(Tag(
        search_result=self,
        value='%s: %s' % (result_field.survey_field.label, result_field.value),
      ))

    self.tags = new_tags
