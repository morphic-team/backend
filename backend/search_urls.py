"""
Search-specific URL generation and validation utilities
"""
import time
import jwt
import os
from urllib.parse import urlencode
from backend.url_signing import generate_signed_url

SERVER_SECRET = os.environ['MORPHIC_SIGNING_SECRET']
PUBLIC_BASE_URL = os.environ['MORPHIC_PUBLIC_BASE_URL']
GOOGLE_SEARCH_BASE_URL = os.environ['GOOGLE_SEARCH_BASE_URL']

# JWT claims constants
JWT_AUDIENCE = 'morphic-browser-extension'
JWT_ISSUER = 'morphic-api'


def generate_upload_google_results_url(user_id, search_id, limit, expires_in=3600):
    """
    Generate signed URL for uploading Google search results
    
    Args:
        user_id: ID of the user requesting access
        search_id: ID of the search being uploaded to
        limit: Maximum number of results to upload
        expires_in: Expiration time in seconds (default 1 hour)
    
    Returns:
        Signed token string (implementation detail hidden)
    """
    expires = int(time.time() + expires_in)
    
    payload = {
        'search_id': search_id,
        'limit': limit,
        'user_id': user_id,
        'iat': int(time.time()),
        'exp': expires,
        'aud': JWT_AUDIENCE,
        'iss': JWT_ISSUER
    }
    
    # Generate the JWT token
    token = jwt.encode(payload, SERVER_SECRET, algorithm='HS256')
    
    # Create a new payload with the upload URL included (no token in URL)
    full_payload = payload.copy()
    full_payload['upload_url'] = f"{PUBLIC_BASE_URL}/api/upload-google-results"
    
    # Return a new JWT with the complete payload
    return jwt.encode(full_payload, SERVER_SECRET, algorithm='HS256')


def verify_upload_google_results_signature(token):
    """
    Verify and decode upload signature
    
    Args:
        token: Signed token string
    
    Returns:
        Decoded payload if valid
        
    Raises:
        jwt.InvalidTokenError on verification failure
    """
    return jwt.decode(token, SERVER_SECRET, algorithms=['HS256'])


def generate_google_search_url(search_query, upload_token):
    """
    Generate a Google Images search URL with embedded upload token
    
    Args:
        search_query: The search query string
        upload_token: Signed upload token
    
    Returns:
        Complete Google Images URL
    """
    query_string = urlencode({'q': search_query})
    
    return f"{GOOGLE_SEARCH_BASE_URL}/search?{query_string}&fg=1&tbm=isch&tbs=itp:photo,morphic:{upload_token}"