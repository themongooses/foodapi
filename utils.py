from datetime import date
from datetime import datetime
from functools import wraps, update_wrapper

from flask import make_response
from simplejson import JSONEncoder
from werkzeug.routing import BaseConverter


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime) or isinstance(obj, date):
                obj = obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return "".join(list(iterable))
        return JSONEncoder.default(self, obj)


class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(value)
                        for value in values)


class DateConverter(BaseConverter):
    def to_python(self, value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    def to_url(self, value):
        return value.isoformat()


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers[
            'Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


def check_date(date):
    try:
        import datetime
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True
