from fastapi import FastAPI
from routes import email_routes

app = FastAPI()

app.include_router(email_routes.router)
