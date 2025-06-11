"""
Shared utilities for generating and verifying signed URLs
"""
import time
import hmac
import hashlib
import os
import jwt
from flask import request, abort
from urllib.parse import urlencode

SERVER_SECRET = os.environ['MORPHIC_SIGNING_SECRET']
PUBLIC_BASE_URL = os.environ['MORPHIC_PUBLIC_BASE_URL']


def generate_signed_url(user_id, resource_id, endpoint, purpose, expires_in=3600):
    """
    Generate a signed URL for accessing protected resources
    
    Args:
        user_id: ID of the user requesting access
        resource_id: ID of the resource being accessed
        endpoint: The endpoint path (e.g., '/api/search_results/{id}/image')
        purpose: Purpose string for key derivation (e.g., 'image_access', 'gather_results')
        expires_in: Expiration time in seconds (default 1 hour)
    
    Returns:
        Complete signed URL with query parameters
    """
    expires = int(time.time() + expires_in)
    
    # Derive a signing key unique to this user and purpose
    user_signing_key = hmac.new(
        SERVER_SECRET.encode(), 
        f"{purpose}_{user_id}".encode(), 
        hashlib.sha256
    ).digest()
    
    # Sign the specific request
    payload = f"{resource_id}:{expires}"
    signature = hmac.new(user_signing_key, payload.encode(), hashlib.sha256).hexdigest()
    
    return f"{endpoint}?u={user_id}&e={expires}&s={signature}"


def verify_signed_url(resource_id, purpose, additional_checks=None):
    """
    Verify a signed URL and return the resource if valid
    
    Args:
        resource_id: ID of the resource being accessed
        purpose: Purpose string used for key derivation
        additional_checks: Optional function to perform additional authorization checks
                          Should accept (user_id, resource_id) and return True if authorized
    
    Returns:
        user_id if verification succeeds
        
    Raises:
        HTTP 403/410/404 via abort() on failure
    """
    user_id = request.args.get('u')
    expires = request.args.get('e')
    signature = request.args.get('s')
    
    if not user_id or not expires or not signature:
        abort(403)
    
    try:
        expires_int = int(expires)
        user_id_int = int(user_id)
    except ValueError:
        abort(403)
    
    # Check expiration
    if expires_int < time.time():
        abort(410)  # Expired
    
    # Re-derive the same signing key for this user and purpose
    user_signing_key = hmac.new(
        SERVER_SECRET.encode(), 
        f"{purpose}_{user_id}".encode(), 
        hashlib.sha256
    ).digest()
    
    # Verify signature
    expected_payload = f"{resource_id}:{expires}"
    expected_sig = hmac.new(user_signing_key, expected_payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        abort(403)
    
    # Perform additional authorization checks if provided
    if additional_checks and not additional_checks(user_id_int, resource_id):
        abort(403)
    
    return user_id_int