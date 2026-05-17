class NoCacheAuthMiddleware:
    """
    Adds Cache-Control: no-store to HTML responses for authenticated users.
    Prevents browsers from caching pages that contain CSRF tokens, which
    causes 403 errors when switching between accounts.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.user.is_authenticated
            and 'text/html' in response.get('Content-Type', '')
            and not response.has_header('Cache-Control')
        ):
            response['Cache-Control'] = 'no-store'
        return response
