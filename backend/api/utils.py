import json
from functools import wraps
from flask_restful import fields


def paginate_marshaller(m):
  return {
    'count': fields.Integer,
    'limit': fields.Integer,
    'offset': fields.Integer,
    'results': fields.Nested(m),
  }

def my_jsonify(f):
  @wraps(f)
  def wrapped(*args, **kwargs):
    raw = f(*args, **kwargs)
    if isinstance(raw, tuple) and len(raw) == 2:
      # Handle (data, status_code) tuples
      data, status_code = raw
      return json.dumps(data), status_code
    else:
      return json.dumps(raw)
  return wrapped
