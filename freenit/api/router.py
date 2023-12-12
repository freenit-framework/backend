from fastapi import FastAPI

from ..decorators import FreenitAPI

api = FastAPI()
route = FreenitAPI(api)
