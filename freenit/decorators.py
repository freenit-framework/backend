import functools


def FreenitAPI(app):
    class route:
        def __init__(self, route, tags=["object"]):
            self.app = app
            self.route = route
            self.tags = tags

        def __call__(self, cls):
            origGet = getattr(cls, "get", None)
            origPost = getattr(cls, "post", None)
            origPatch = getattr(cls, "patch", None)
            origDelete = getattr(cls, "delete", None)

            class Wrapped(cls):
                tags = self.tags
                tag = tags[0]
                if callable(origGet):
                    _deco = self.app.get(
                        self.route,
                        summary=getattr(origGet, "description", f"Get {tag}"),
                        tags=tags,
                    )
                    get = _deco(origGet)
                if callable(origPost):
                    _deco = self.app.post(
                        self.route,
                        summary=getattr(origPost, "description", f"Create {tag}"),
                        tags=tags,
                    )
                    post = _deco(origPost)
                if callable(origPatch):
                    _deco = self.app.patch(
                        self.route,
                        summary=getattr(origPatch, "description", f"Edit {tag}"),
                        tags=tags,
                    )
                    patch = _deco(origPatch)
                if callable(origDelete):
                    _deco = self.app.delete(
                        self.route,
                        summary=getattr(origDelete, "description", f"Destroy {tag}"),
                        tags=tags,
                    )
                    delete = _deco(origDelete)
                _deco = None

            return Wrapped

    return route


def description(desc: str):
    def decorator(func):
        @functools.wraps(func)
        async def endpoint(*args, **kwargs):
            return await func(*args, **kwargs)

        setattr(endpoint, "description", desc)
        return endpoint

    return decorator
