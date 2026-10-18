from flask import Blueprint, request, Response, stream_template
import requests
from config import config
from services.auth import get_auth_headers
import mimetypes
import os
from urllib.parse import unquote
import re

proxy_bp = Blueprint('proxy', __name__)

@proxy_bp.route('/data/<path:filename>')
def proxy_content(filename):
    """Proxy content file requests, supporting HTTP Range requests for video streaming"""
    # Decode the filename
    filename = unquote(filename)
    
    # Build the internal URL
    internal_url = f"{config.SZURUBOORU_URL}data/{filename}"
    
    # Get the client's Range header
    range_header = request.headers.get('Range')
    headers = {}
    
    # If the client sent a Range header, forward it to the backend
    if range_header:
        headers['Range'] = range_header
    
    try:
        # Fetch the file from the internal server
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # Support 206 Partial Content
            # Get the file's MIME type
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    # Use the file extension for a more accurate MIME type
                    ext = filename.lower().split('.')[-1]
                    if ext in ['mp4']:
                        content_type = 'video/mp4'
                    elif ext in ['webm']:
                        content_type = 'video/webm'
                    elif ext in ['avi']:
                        content_type = 'video/avi'
                    elif ext in ['mov']:
                        content_type = 'video/quicktime'
                    else:
                        content_type = 'application/octet-stream'
            
            # Create the response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Build response headers
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=31536000',  # Cache for one year
            }
            
            # Pass through important headers
            if response.headers.get('Content-Length'):
                response_headers['Content-Length'] = response.headers.get('Content-Length')
            if response.headers.get('Content-Range'):
                response_headers['Content-Range'] = response.headers.get('Content-Range')
            if response.headers.get('Accept-Ranges'):
                response_headers['Accept-Ranges'] = response.headers.get('Accept-Ranges')
            if response.headers.get('ETag'):
                response_headers['ETag'] = response.headers.get('ETag')
            if response.headers.get('Last-Modified'):
                response_headers['Last-Modified'] = response.headers.get('Last-Modified')
            
            # For video files, make sure Range requests are supported
            ext = filename.lower().split('.')[-1]
            if ext in ['mp4', 'webm', 'avi', 'mov', 'mkv']:
                response_headers['Accept-Ranges'] = 'bytes'
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers=response_headers
            )
            
            return proxy_response
        else:
            return Response('File not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for {filename}: {e}")
        return Response('Internal server error', status=500)

@proxy_bp.route('/thumbnails/<path:filename>')
def proxy_thumbnail(filename):
    """Proxy thumbnail requests"""
    # Decode the filename
    filename = unquote(filename)
    
    # Build the internal URL
    internal_url = f"{config.SZURUBOORU_URL}thumbnails/{filename}"
    
    # Get the client's Range header
    range_header = request.headers.get('Range')
    headers = {}
    
    # If the client sent a Range header, forward it to the backend
    if range_header:
        headers['Range'] = range_header
    
    try:
        # Fetch the file from the internal server
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # Support 206 Partial Content
            # Get the file's MIME type
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'image/jpeg'  # Thumbnails are usually JPEG
            
            # Create the response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Build response headers
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=31536000',  # Cache for one year
            }
            
            # Pass through important headers
            if response.headers.get('Content-Length'):
                response_headers['Content-Length'] = response.headers.get('Content-Length')
            if response.headers.get('Content-Range'):
                response_headers['Content-Range'] = response.headers.get('Content-Range')
            if response.headers.get('Accept-Ranges'):
                response_headers['Accept-Ranges'] = response.headers.get('Accept-Ranges')
            if response.headers.get('ETag'):
                response_headers['ETag'] = response.headers.get('ETag')
            if response.headers.get('Last-Modified'):
                response_headers['Last-Modified'] = response.headers.get('Last-Modified')
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers=response_headers
            )
            
            return proxy_response
        else:
            return Response('Thumbnail not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for thumbnail {filename}: {e}")
        return Response('Internal server error', status=500)

@proxy_bp.route('/avatars/<path:filename>')
def proxy_avatar(filename):
    """Proxy avatar requests"""
    # Decode the filename
    filename = unquote(filename)
    
    # Build the internal URL
    internal_url = f"{config.SZURUBOORU_URL}avatars/{filename}"
    
    # Get the client's Range header
    range_header = request.headers.get('Range')
    headers = {}
    
    # If the client sent a Range header, forward it to the backend
    if range_header:
        headers['Range'] = range_header
    
    try:
        # Fetch the file from the internal server
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # Support 206 Partial Content
            # Get the file's MIME type
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'image/png'  # Avatars are usually PNG
            
            # Create the response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # Build response headers
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=86400',  # Cache for one day
            }
            
            # Pass through important headers
            if response.headers.get('Content-Length'):
                response_headers['Content-Length'] = response.headers.get('Content-Length')
            if response.headers.get('Content-Range'):
                response_headers['Content-Range'] = response.headers.get('Content-Range')
            if response.headers.get('Accept-Ranges'):
                response_headers['Accept-Ranges'] = response.headers.get('Accept-Ranges')
            if response.headers.get('ETag'):
                response_headers['ETag'] = response.headers.get('ETag')
            if response.headers.get('Last-Modified'):
                response_headers['Last-Modified'] = response.headers.get('Last-Modified')
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers=response_headers
            )
            
            return proxy_response
        else:
            return Response('Avatar not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for avatar {filename}: {e}")
        return Response('Internal server error', status=500) 