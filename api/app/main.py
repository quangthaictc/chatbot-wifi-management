#!/usr/bin/env python

from fastapi import FastAPI
from app.routes import network


app = FastAPI()

app.include_router(network.router)
