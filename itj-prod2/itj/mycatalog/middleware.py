from django.http import HttpResponsePermanentRedirect


class NoWWWRedirectMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_request(self, request):
        host = request.get_host()
        if host.startswith('www.'):
            if request.method == 'GET':
                no_www_host = host[4:]
                url = request.build_absolute_uri().replace(host, no_www_host, 1)
                return HttpResponsePermanentRedirect(url)
