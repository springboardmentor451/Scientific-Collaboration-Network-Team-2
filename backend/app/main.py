from fastapi import FastAPI
from .database.connection import engine, test_connection
from .database.base import Base

# Import models so SQLAlchemy knows about them
from .models.user import *

app = FastAPI(
    title="Scientific Collaboration Network Analyzer"
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Scientific Collaboration Network Analyzer"}

@app.get("/db-test")
def db_test():
    if test_connection():
        return {
            "status": "success",
            "message": "Database connected successfully!"
        }

    return {
        "status": "failed",
        "message": "Database connection failed!"
    }