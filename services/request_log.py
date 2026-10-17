import logging
import time
from urllib.parse import urlencode
from flask import request, g

logger = logging.getLogger('request_log')

# 日志中隐藏的敏感参数
SENSITIVE_PARAMS = {'api_key', 'password', 'password_hash', 'token'}
SLOW_THRESHOLD_MS = 1000
BODY_PREVIEW_LIMIT = 500


def _redacted_query():
    if not request.args:
        return ''
    items = [(k, '***' if k.lower() in SENSITIVE_PARAMS else v)
             for k, v in request.args.items(multi=True)]
    return '?' + urlencode(items)


def _body_preview():
    data = request.get_data(cache=True, as_text=True)
    if not data:
        return ''
    if request.is_json:
        body = request.get_json(silent=True)
        if isinstance(body, dict):
            body = {k: ('***' if k.lower() in SENSITIVE_PARAMS else v) for k, v in body.items()}
            data = str(body)
    return data[:BODY_PREVIEW_LIMIT]


def init_request_logging(app):
    """记录每个请求的方法、路径、状态码、耗时；未匹配路由的请求标记为 UNMATCHED"""

    @app.before_request
    def _start_timer():
        g._request_start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        start = getattr(g, '_request_start', None)
        duration = (time.perf_counter() - start) * 1000 if start else -1
        matched = request.url_rule is not None

        tags = []
        if not matched:
            tags.append('UNMATCHED')
        if duration >= SLOW_THRESHOLD_MS:
            tags.append('SLOW')
        tag_str = f" [{','.join(tags)}]" if tags else ''

        client = request.headers.get('X-Forwarded-For', request.remote_addr)
        logger.info(
            f"{request.method} {request.path}{_redacted_query()} -> {response.status_code} "
            f"{duration:.1f}ms {response.calculate_content_length() or '-'}B "
            f"client={client} endpoint={request.endpoint or '-'}{tag_str} "
            f"ua=\"{request.headers.get('User-Agent', '-')}\""
        )
        if not matched or response.status_code >= 400:
            body = _body_preview()
            if body:
                logger.info(f"    body: {body}")
        return response
