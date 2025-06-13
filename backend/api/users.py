import json
from functools import wraps
from flask import Blueprint, jsonify, request
from flask_restful import marshal_with, fields, reqparse
from backend import db
from backend.models import Survey, User, Session, SurveyField
from backend.api.utils import my_jsonify, paginate_marshaller
from backend.auth import require_auth

users_bp = Blueprint('users', __name__)

@users_bp.route('/users', methods=["POST"])
@my_jsonify
@marshal_with({'user': fields.Nested(User.marshaller), 'session': fields.Nested(Session.marshaller)})
def sign_up():
  parser = reqparse.RequestParser()
  parser.add_argument('email_address')
  parser.add_argument('password')
  args = parser.parse_args()

  if not args.email_address or not args.password:
    return {'error': 'Email and password are required'}, 400
  
  # Check if email already exists
  existing_user = User.query.filter(User.email_address==args.email_address).first()
  if existing_user:
    return {'error': 'An account with this email address already exists'}, 409
  
  # Basic password validation
  if len(args.password) < 6:
    return {'error': 'Password must be at least 6 characters long'}, 400

  user = User(email_address=args.email_address)
  user.set_password(args.password)
  db.session.add(user)

  session = user.create_new_session()
  db.session.add(session)

  db.session.commit()

  return {'user': user, 'session': session}

@users_bp.route('/users/<int:user_id>/surveys')
@require_auth
@my_jsonify
@marshal_with(paginate_marshaller(Survey.marshaller))
def get_users_surveys(user_id):
  # Parse is_archived parameter (defaults to showing non-archived)
  is_archived_param = request.args.get('is_archived')
  
  query = Survey.query.filter(Survey.user_id == user_id)
  
  # Filter by archive status
  if is_archived_param is not None:
    is_archived = is_archived_param.lower() == 'true'
    query = query.filter(Survey.is_archived == is_archived)
  else:
    # Default: show only non-archived surveys
    query = query.filter(Survey.is_archived == False)
  
  users_surveys = query.all()
  return {
    'results': users_surveys
  }

@users_bp.route('/users/<int:user_id>/surveys', methods=['POST'])
@require_auth
@my_jsonify
@marshal_with(Survey.marshaller)
def user_create_survey(user_id):
  parser = reqparse.RequestParser()
  parser.add_argument('name', type=str)
  parser.add_argument('comments', type=str)
  parser.add_argument('fields', location='json', type=list)
  args = parser.parse_args()
  survey = Survey(
    user_id=user_id,
    name=args.name,
    comments=args.comments,
  )

  for survey_field_arg in args.fields:
    survey_field = SurveyField(
      survey=survey,
      label=survey_field_arg['label'],
      field_type=survey_field_arg['field_type'],
      order=survey_field_arg.get('order', 1),
    )
    if 'options' in survey_field_arg:
      survey_field.options=json.dumps(survey_field_arg['options'])
    db.session.add(survey_field)
  db.session.add(survey)
  db.session.commit()
  return survey