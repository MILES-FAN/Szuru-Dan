from flask import request
from config import config

def get_current_domain():
    """动态获取当前请求的域名"""
    if config.REVERSE_PROXY_MODE:
        # 在反向代理模式下，使用当前请求的域名
        scheme = request.scheme
        host = request.host
        return f"{scheme}://{host}/"
    else:
        # 普通模式下使用配置的域名
        return config.DOMAIN_URL

def build_resource_url(resource_path):
    """构建资源URL"""
    if config.REVERSE_PROXY_MODE:
        # 反向代理模式：使用当前域名
        return f"{get_current_domain()}{resource_path}"
    else:
        return f"{config.DOMAIN_URL}{resource_path}"