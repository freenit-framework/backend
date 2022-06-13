import functools


def FreenitAPI(app):
    class route:
        def __init__(self, route, tags=["object"], responses={}):
            self.app = app
            self.route = route
            self.tags = tags
            self.responses = responses

        def __call__(self, cls):
            origGet = getattr(cls, "get", None)
            origPost = getattr(cls, "post", None)
            origPatch = getattr(cls, "patch", None)
            origDelete = getattr(cls, "delete", None)
            app = self.app
            responses = self.responses

            class Wrapped(cls):
                if callable(origGet):
                    _deco = app.get(
                        self.route,
                        summary=getattr(origGet, "description", f"Get {self.tags[0]}"),
                        response_model=responses.get("get")
                        or origGet.__annotations__.get("return"),
                        tags=self.tags,
                    )
                    get = _deco(origGet)
                if callable(origPost):
                    _deco = self.app.post(
                        self.route,
                        summary=getattr(
                            origPost, "description", f"Create {self.tags[0]}"
                        ),
                        response_model=responses.get("post")
                        or origPost.__annotations__.get("return"),
                        tags=self.tags,
                    )
                    post = _deco(origPost)
                if callable(origPatch):
                    _deco = self.app.patch(
                        self.route,
                        summary=getattr(
                            origPatch, "description", f"Edit {self.tags[0]}"
                        ),
                        response_model=responses.get("patch")
                        or origPatch.__annotations__.get("return"),
                        tags=self.tags,
                    )
                    patch = _deco(origPatch)
                if callable(origDelete):
                    _deco = self.app.delete(
                        self.route,
                        summary=getattr(
                            origDelete, "description", f"Destroy {self.tags[0]}"
                        ),
                        response_model=responses.get("delete")
                        or origDelete.__annotations__.get("return"),
                        tags=self.tags,
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
