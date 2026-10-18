from flask import request
from config import config

def get_current_domain():
    """Dynamically get the domain of the current request"""
    if config.REVERSE_PROXY_MODE:
        # In reverse proxy mode, use the current request's domain
        scheme = request.scheme
        host = request.host
        return f"{scheme}://{host}/"
    else:
        # In normal mode, use the configured domain
        return config.DOMAIN_URL

def build_resource_url(resource_path):
    """Build a resource URL"""
    if config.REVERSE_PROXY_MODE:
        # Reverse proxy mode: use the current domain
        return f"{get_current_domain()}{resource_path}"
    else:
        return f"{config.DOMAIN_URL}{resource_path}"