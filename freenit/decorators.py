class route:
    def __init__(self, app, route, models, tags=[], many=False):
        self.app = app
        self.route = route
        self.models = models
        self.tags = tags
        self.many = many

    def __call__(self, cls, *args, **kwargs):
        origFetch = getattr(cls, "fetch", None)
        origCreate = getattr(cls, "create", None)
        origEdit = getattr(cls, "edit", None)
        origDestroy = getattr(cls, "destroy", None)
        fetchSuffix = " list" if self.many else ""
        models = self.models
        mname = models.base.__name__
        modelName = mname[:-4] if mname.endswith("Base") else mname
        fetchModel = models.listing if self.many else models.response
        fetchDeco = self.app.get(
            self.route,
            summary=f"Get {modelName}{fetchSuffix}",
            response_model=fetchModel,
            tags=self.tags,
        )
        createDeco = self.app.post(
            self.route,
            summary=f"Create {modelName}",
            response_model=models.response,
            tags=self.tags,
        )
        editDeco = self.app.patch(
            self.route,
            summary=f"Edit {modelName}",
            response_model=models.response,
            tags=self.tags,
        )
        destroyDeco = self.app.delete(
            self.route,
            summary=f"Destroy {modelName}",
            response_model=models.response,
            tags=self.tags,
        )

        class Wrapped(cls):
            if callable(origFetch):
                fetch = fetchDeco(origFetch)
            if callable(origCreate):
                create = createDeco(origCreate)
            if callable(origEdit):
                edit = editDeco(origEdit)
            if callable(origDestroy):
                destroy = destroyDeco(origDestroy)

        return Wrapped

