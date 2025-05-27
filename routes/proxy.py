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
    """代理内容文件请求，支持HTTP Range请求用于视频流播放"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}data/{filename}"
    
    # 获取客户端的Range请求头
    range_header = request.headers.get('Range')
    headers = {}
    
    # 如果客户端发送了Range请求，转发给后端
    if range_header:
        headers['Range'] = range_header
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # 支持206 Partial Content
            # 获取文件的MIME类型
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    # 根据文件扩展名设置更准确的MIME类型
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
            
            # 创建响应
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            # 构建响应头
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=31536000',  # 缓存一年
            }
            
            # 传递重要的头部信息
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
            
            # 对于视频文件，确保支持Range请求
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
    """代理缩略图请求"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}thumbnails/{filename}"
    
    # 获取客户端的Range请求头
    range_header = request.headers.get('Range')
    headers = {}
    
    # 如果客户端发送了Range请求，转发给后端
    if range_header:
        headers['Range'] = range_header
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # 支持206 Partial Content
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
            
            # 构建响应头
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=31536000',  # 缓存一年
            }
            
            # 传递重要的头部信息
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
    """代理头像请求"""
    # 解码文件名
    filename = unquote(filename)
    
    # 构建内网URL
    internal_url = f"{config.SZURUBOORU_URL}avatars/{filename}"
    
    # 获取客户端的Range请求头
    range_header = request.headers.get('Range')
    headers = {}
    
    # 如果客户端发送了Range请求，转发给后端
    if range_header:
        headers['Range'] = range_header
    
    try:
        # 从内网服务器获取文件
        response = requests.get(internal_url, headers=headers, stream=True, timeout=30)
        
        if response.status_code in [200, 206]:  # 支持206 Partial Content
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
            
            # 构建响应头
            response_headers = {
                'Content-Type': content_type,
                'Cache-Control': 'public, max-age=86400',  # 缓存一天
            }
            
            # 传递重要的头部信息
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