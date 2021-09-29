class ModelsBase:
    def __init__(self, base, response=None, listing=None):
        self.base = base
        self.response = response if response is not None else base
        self.listing = listing if listing is not None else base
