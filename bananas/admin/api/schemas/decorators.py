def tags(include=None, exclude=None):
    def decorator(view):
        view.include_tags = include
        view.exclude_tags = exclude
        return view

    return decorator
