from fastapi import FastAPI
from freenit.config import getConfig
from .api import api

config = getConfig()
app = FastAPI()
app.mount("/api/v1", api)
