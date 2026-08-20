from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db
from backend.app.api.v1.endpoints import (
    auth, users, institutions, departments, researchers,
    publications, publication_authors, projects, project_assignments,
    collaborations, conferences, conference_participation, citations,
    references, network, dashboards, reports, audit_logs, search, notifications
)

# Prometheus metrics setup
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP Requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "endpoint"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and seed admin user
    try:
        db = SessionLocal()
        init_db(db)
        db.close()
    except Exception as e:
        print(f"Database initialization skipped: {e}")
    yield

import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/api/v1/publications/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for metrics logging
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Exclude /metrics from logging
    endpoint = request.url.path
    if endpoint != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            http_status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
    return response

# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(users.router, prefix=settings.API_V1_STR, tags=["users"])
app.include_router(institutions.router, prefix=settings.API_V1_STR, tags=["institutions"])
app.include_router(departments.router, prefix=settings.API_V1_STR, tags=["departments"])
app.include_router(researchers.router, prefix=settings.API_V1_STR, tags=["researchers"])
app.include_router(publications.router, prefix=settings.API_V1_STR, tags=["publications"])
app.include_router(publication_authors.router, prefix=settings.API_V1_STR, tags=["publication-authors"])
app.include_router(projects.router, prefix=settings.API_V1_STR, tags=["projects"])
app.include_router(project_assignments.router, prefix=settings.API_V1_STR, tags=["project-assignments"])
app.include_router(collaborations.router, prefix=settings.API_V1_STR, tags=["collaborations"])
app.include_router(conferences.router, prefix=settings.API_V1_STR, tags=["conferences"])
app.include_router(conference_participation.router, prefix=settings.API_V1_STR, tags=["conference-participation"])
app.include_router(citations.router, prefix=settings.API_V1_STR, tags=["citations"])
app.include_router(references.router, prefix=settings.API_V1_STR, tags=["references"])
app.include_router(network.router, prefix=settings.API_V1_STR, tags=["network"])
app.include_router(dashboards.router, prefix=settings.API_V1_STR, tags=["dashboards"])
app.include_router(reports.router, prefix=settings.API_V1_STR, tags=["reports"])
app.include_router(audit_logs.router, prefix=settings.API_V1_STR, tags=["audit-logs"])
app.include_router(search.router, prefix=settings.API_V1_STR, tags=["search"])
app.include_router(notifications.router, prefix=settings.API_V1_STR, tags=["notifications"])
