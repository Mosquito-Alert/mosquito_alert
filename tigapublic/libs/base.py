"""Base classes for all API calls."""
# -*- coding: utf-8 -*-
import json
from io import BytesIO
import gzip

from django.http import HttpResponse

from tigapublic.utils import CustomJSONEncoder, extendUser


class BaseManager(object):
    """Common functions to all API classes.

    Attributes:
    - request => The Request object. The request.user is an extended object, it
        has all custom methods (is_root(), is_manager(), ...)
    - response => The content to return as an HttpResponse.
    - status => The status code to return as an HttpResponse.

    Methods:
    - _end() => Return an HttpResponse to the client.
    - _end_unauthorized() => Return an HttpResponse with a status code of 401
        and a JSON with an attribute 'desc' whos evalue is the string
        'Unauthorized'.
    """

    response = {}
    status = 200

    def __init__(self, request):
        """Constructor."""
        request.user = extendUser(request.user)
        self.request = request

    def _end_unauthorized(self):
        """Return an Unauthorized response and finish."""
        self.response['desc'] = 'Unauthorized'
        self.status = 401
        return self._end()

    def _end(self):
        """Finish the process.

        Output an HttpResponse with self.response as the content and
        self.status as status code.
        """
        return HttpResponse(
            json.dumps(self.response, cls=CustomJSONEncoder),
            content_type='application/json',
            status=self.status
        )

    def _end_gz(self):
        """Finish the process.

        ZIP Output an HttpResponse with self.response as the content and
        self.status as status code.
        """
        zbuf = BytesIO()
        zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        content = json.dumps(self.response, cls=CustomJSONEncoder)
        zfile.write(content.encode('utf-8'))
        zfile.close()

        compressed_content = zbuf.getvalue()
        response = HttpResponse(compressed_content)
        response['Content-Encoding'] = 'gzip'
        response['Content-Length'] = str(len(compressed_content))
        return response
