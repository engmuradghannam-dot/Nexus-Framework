from rest_framework import versioning
from rest_framework.exceptions import APIException

class NexusURLPathVersioning(versioning.URLPathVersioning):
    """Custom URL path versioning for Nexus Framework"""
    default_version = 'v1'
    allowed_versions = ['v1', 'v2', 'v3']
    version_param = 'version'

class InvalidVersion(APIException):
    status_code = 400
    default_detail = 'Invalid API version specified.'
    default_code = 'invalid_version'

class NexusHeaderVersioning(versioning.AcceptHeaderVersioning):
    """Header-based versioning with deprecation support"""
    default_version = 'v1'
    allowed_versions = ['v1', 'v2', 'v3']
    VERSION_ALIASES = {
        'latest': 'v3',
        'stable': 'v2',
        'legacy': 'v1',
    }
    DEPRECATED_VERSIONS = {'v1'}

class VersionDeprecationMiddleware:
    """Add deprecation warnings for old API versions"""
    DEPRECATION_MESSAGES = {
        'v1': 'API v1 is deprecated. Please migrate to v2 or v3.',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if hasattr(request, 'version') and request.version in self.DEPRECATION_MESSAGES:
            response['X-API-Deprecated'] = 'true'
            response['X-API-Deprecation-Message'] = self.DEPRECATION_MESSAGES[request.version]

        return response
