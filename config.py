import configparser
import sys

class Config:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        self.SZURUBOORU_URL = config['API']['backend_url']
        if not self.SZURUBOORU_URL.endswith('/'):
            self.SZURUBOORU_URL += '/'
        
        # Check whether reverse proxy mode is enabled
        self.REVERSE_PROXY_MODE = config.getboolean('API', 'reverse_proxy_mode', fallback=False)
        
        # Check whether timing logs are enabled
        self.ENABLE_TIMING_LOGS = config.getboolean('API', 'enable_timing_logs', fallback=False)
        
        if not self.REVERSE_PROXY_MODE:
            # Normal mode: use the configured domain
            self.DOMAIN_URL = ''
            if 'domain_url' in config['API'] and config['API']['domain_url'] != '':
                self.DOMAIN_URL = config['API']['domain_url']
                if not self.DOMAIN_URL.endswith('/'):
                    self.DOMAIN_URL += '/'
            else:
                self.DOMAIN_URL = self.SZURUBOORU_URL
        else:
            # Reverse proxy mode: the domain is resolved per request, so leave it empty here
            self.DOMAIN_URL = ''
        
        self.SERVICE_PORT = int(config['API']['port'])
        self.SZURUBOORU_API_URL = f'{self.SZURUBOORU_URL}api'

        # Print config info - write to sys.stdout and flush
        config_info = f"""
=== Configuration Loaded ===
Szurubooru URL: {self.SZURUBOORU_URL}
Service Port: {self.SERVICE_PORT}
Reverse Proxy Mode: {self.REVERSE_PROXY_MODE}
Domain URL: {self.DOMAIN_URL}
Enable Timing Logs: {self.ENABLE_TIMING_LOGS}
============================
"""
        print(config_info, flush=True)
        sys.stdout.flush()

# Global config instance
config = Config() 