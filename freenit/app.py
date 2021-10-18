from fastapi import FastAPI

from .api import api
from .config import getConfig

config = getConfig()
app = FastAPI()
app.mount("/api/v1", api)
