from flask import Blueprint, request, Response, stream_template
import requests
from config import config
from services.auth import get_auth_headers
import mimetypes
import os
from urllib.parse import unquote

proxy_bp = Blueprint('proxy', __name__)

@proxy_bp.route('/data/<path:filename>')
def proxy_content(filename):
    """代理内容文件请求"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}data/{filename}"
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            # 获取文件的MIME类型
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # 创建响应
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers={
                    'Content-Type': content_type,
                    'Content-Length': response.headers.get('Content-Length'),
                    'Cache-Control': 'public, max-age=31536000',  # 缓存一年
                    'ETag': response.headers.get('ETag'),
                    'Last-Modified': response.headers.get('Last-Modified'),
                }
            )
            
            return proxy_response
        else:
            return Response('File not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for {filename}: {e}")
        return Response('Internal server error', status=500)

@proxy_bp.route('/thumbnails/<path:filename>')
def proxy_thumbnail(filename):
    """代理缩略图请求"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}thumbnails/{filename}"
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            # 获取文件的MIME类型
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'image/jpeg'  # 缩略图通常是JPEG
            
            # 创建响应
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers={
                    'Content-Type': content_type,
                    'Content-Length': response.headers.get('Content-Length'),
                    'Cache-Control': 'public, max-age=31536000',  # 缓存一年
                    'ETag': response.headers.get('ETag'),
                    'Last-Modified': response.headers.get('Last-Modified'),
                }
            )
            
            return proxy_response
        else:
            return Response('Thumbnail not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for thumbnail {filename}: {e}")
        return Response('Internal server error', status=500)

@proxy_bp.route('/avatars/<path:filename>')
def proxy_avatar(filename):
    """代理头像请求"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}avatars/{filename}"
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            # 获取文件的MIME类型
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'image/png'  # 头像通常是PNG
            
            # 创建响应
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            proxy_response = Response(
                generate(),
                status=response.status_code,
                headers={
                    'Content-Type': content_type,
                    'Content-Length': response.headers.get('Content-Length'),
                    'Cache-Control': 'public, max-age=86400',  # 缓存一天
                    'ETag': response.headers.get('ETag'),
                    'Last-Modified': response.headers.get('Last-Modified'),
                }
            )
            
            return proxy_response
        else:
            return Response('Avatar not found', status=404)
            
    except requests.exceptions.RequestException as e:
        print(f"Proxy error for avatar {filename}: {e}")
        return Response('Internal server error', status=500) 