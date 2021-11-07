def FreenitAPI(app):
    class route:
        def __init__(self, route, tags=["object"], many=False, responses={}):
            self.app = app
            self.route = route
            self.tags = tags
            self.many = many
            self.responses = responses

        def __call__(self, cls):
            origGet = getattr(cls, "get", None)
            origPost = getattr(cls, "post", None)
            origPatch = getattr(cls, "patch", None)
            origDelete = getattr(cls, "delete", None)
            getSuffix = " list" if self.many else ""
            app = self.app
            responses = self.responses

            class Wrapped(cls):
                if callable(origGet):
                    anotated_model = origGet.__annotations__.get("return")
                    model = responses.get("get") or anotated_model
                    deco = app.get(
                        self.route,
                        summary=f"Get {self.tags[0]}{getSuffix}",
                        response_model=model,
                        tags=self.tags,
                    )
                    get = deco(origGet)
                if callable(origPost):
                    anotated_model = origPost.__annotations__.get("return")
                    model = responses.get("post") or anotated_model
                    deco = self.app.post(
                        self.route,
                        summary=f"Create {self.tags[0]}",
                        response_model=model,
                        tags=self.tags,
                    )
                    post = deco(origPost)
                if callable(origPatch):
                    anotated_model = origPatch.__annotations__.get("return")
                    model = responses.get("patch") or anotated_model
                    deco = self.app.patch(
                        self.route,
                        summary=f"Edit {self.tags[0]}",
                        response_model=model,
                        tags=self.tags,
                    )
                    patch = deco(origPatch)
                if callable(origDelete):
                    anotated_model = origDelete.__annotations__.get("return")
                    model = responses.get("delete") or anotated_model
                    deco = self.app.delete(
                        self.route,
                        summary=f"Destroy {self.tags[0]}",
                        response_model=model,
                        tags=self.tags,
                    )
                    delete = deco(origDelete)

            return Wrapped

    return route
