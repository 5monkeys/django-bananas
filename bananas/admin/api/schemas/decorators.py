from functools import wraps


def tags(include=None, exclude=None):
    def wrapped(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            return view(*args, **kwargs)

        wrapper.include_tags = include
        wrapper.exclude_tags = exclude
        return wrapper

    return wrapped
