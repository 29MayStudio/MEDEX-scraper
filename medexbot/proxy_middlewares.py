from w3lib.http import basic_auth_header
from scrapy.utils.project import get_project_settings


class ProxyMiddleware(object):
    def process_request(self, request, spider):
        settings = get_project_settings()
        proxy_host = settings.get('PROXY_HOST')
        proxy_port = settings.get('PROXY_PORT')
        if proxy_host and proxy_port:
            request.meta['proxy'] = proxy_host + ':' + proxy_port
            proxy_user = settings.get('PROXY_USER')
            proxy_password = settings.get('PROXY_PASSWORD')
            if proxy_user and proxy_password:
                request.headers["Proxy-Authorization"] = basic_auth_header(proxy_user, proxy_password)
            spider.log('Proxy : %s' % request.meta['proxy'])
