from fastapi import FastAPI
from backend.app.database.connection import test_connection

app = FastAPI(
    title="Scientific Collaboration Network Analyzer"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to Scientific Collaboration Network Analyzer"
    }

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