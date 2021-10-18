def FreenitAPI(app):
    class route:
        def __init__(self, route, tags=["object"], many=False):
            self.app = app
            self.route = route
            self.tags = tags
            self.many = many

        def __call__(self, cls):
            origGet = getattr(cls, "get", None)
            origPost = getattr(cls, "post", None)
            origPatch = getattr(cls, "patch", None)
            origDelete = getattr(cls, "delete", None)
            getSuffix = " list" if self.many else ""
            getDeco = self.app.get(
                self.route,
                summary=f"Get {self.tags[0]}{getSuffix}",
                response_model=origGet.__annotations__.get("return")
                if origGet
                else None,
                tags=self.tags,
            )
            postDeco = self.app.post(
                self.route,
                summary=f"Create {self.tags[0]}",
                response_model=origPost.__annotations__.get("return")
                if origPost
                else None,
                tags=self.tags,
            )
            patchDeco = self.app.patch(
                self.route,
                summary=f"Edit {self.tags[0]}",
                response_model=origPatch.__annotations__.get("return")
                if origPatch
                else None,
                tags=self.tags,
            )
            deleteDeco = self.app.delete(
                self.route,
                summary=f"Destroy {self.tags[0]}",
                response_model=origDelete.__annotations__.get("return")
                if origDelete
                else None,
                tags=self.tags,
            )

            class Wrapped(cls):
                if callable(origGet):
                    get = getDeco(origGet)
                if callable(origPost):
                    post = postDeco(origPost)
                if callable(origPatch):
                    patch = patchDeco(origPatch)
                if callable(origDelete):
                    delete = deleteDeco(origDelete)

            return Wrapped

    return route
