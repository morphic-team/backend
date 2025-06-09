from flask import abort, Blueprint
from flask_restful import fields, marshal_with, reqparse
from backend import db
from backend.models import User, Session
from backend.api.utils import my_jsonify

sessions_bp = Blueprint('sessions', __name__)


@sessions_bp.route('/sessions', methods=["POST"])
@my_jsonify
@marshal_with({'user': fields.Nested(User.marshaller), 'session': fields.Nested(Session.marshaller)})
def create_session():
  parser = reqparse.RequestParser()
  parser.add_argument('email_address')
  parser.add_argument('password')
  args = parser.parse_args()

  user = User.query.filter(User.email_address==args.email_address).first()
  if user and user.has_password(args.password):
    session = Session(user=user)
    db.session.add(session)
    db.session.commit()  # Commit to generate ID and persist token
    return {
      'user': user,
      'session': session,
    }
  else:
    abort(403)
