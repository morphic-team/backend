from flask import abort, Blueprint
from flask_restful import fields, marshal_with, reqparse
from backend import db
from backend.models import User, Session
from backend.api.utils import my_jsonify

sessions_bp = Blueprint('sessions', __name__)


@sessions_bp.route('/sessions', methods=["POST"])
@my_jsonify
def create_session():
  parser = reqparse.RequestParser()
  parser.add_argument('email_address')
  parser.add_argument('password')
  args = parser.parse_args()

  if not args.email_address or not args.password:
    return {'error': 'Email and password are required'}, 400
  
  user = User.query.filter(User.email_address==args.email_address).first()
  if not user:
    return {'error': 'Invalid email or password'}, 401
  
  if not user.has_password(args.password):
    return {'error': 'Invalid email or password'}, 401
  
  session = Session(user=user)
  db.session.add(session)
  db.session.commit()  # Commit to generate ID and persist token
  
  # Apply marshalling only to successful response
  from flask_restful import marshal
  marshaller = {'user': fields.Nested(User.marshaller), 'session': fields.Nested(Session.marshaller)}
  return marshal({
    'user': user,
    'session': session,
  }, marshaller)
