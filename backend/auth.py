"""
Authentication utilities for API endpoints
"""
from functools import wraps
from flask import request, abort, g
from backend.models import Session


def require_auth(f):
  """Decorator to require session-based authentication"""
  @wraps(f)
  def decorated_function(*args, **kwargs):
    # Get session token from header
    session_token = request.headers.get('X-Session-Token')
    if not session_token:
      abort(401)
    
    # Look up session by token
    session = Session.query.filter(Session.token == session_token).first()
    if not session:
      abort(401)
    
    # Store current user in Flask's g object for use in endpoint
    g.current_user = session.user
    g.current_session = session
    
    return f(*args, **kwargs)
  return decorated_function