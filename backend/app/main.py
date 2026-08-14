from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.connection import engine, test_connection
from .database.base import Base
from .routes.auth import router as auth_router
from .routes.researcher import router as researcher_router

# Import models so SQLAlchemy knows about them
from .models.users import *
from .models.researchers import Researcher
from .models.institutions import Institution

app = FastAPI(
    title="Scientific Collaboration Network Analyzer"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(auth_router)
app.include_router(researcher_router)
