import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.migrations import run_startup_migrations

from fastapi.staticfiles import StaticFiles
import os



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=(
        r"^(https://.*\.vercel\.app|"
        r"http://localhost:\d+|"
        r"http://127\.0\.0\.1:\d+|"
        r"http://192\.168\.\d{1,3}\.\d{1,3}:\d+|"
        r"http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+|"
        r"http://172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}:\d+)$"
    ),
    allow_credentials="*" not in settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    """Allow public origins to call private/local network addresses.

    Chromium's Private Network Access (PNA) blocks requests from public
    origins to private/local addresses unless the server responds with
    `Access-Control-Allow-Private-Network: true`. Starlette's
    CORSMiddleware does not emit this header, so we add it here whenever
    CORS headers are present (i.e. CORSMiddleware handled the response).
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if "access-control-allow-origin" in response.headers:
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response


app.add_middleware(PrivateNetworkAccessMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)

logger = logging.getLogger(__name__)

# Enable debug logging for the server
logger.setLevel(logging.DEBUG)


@app.on_event("startup")
async def startup_migrations():
    await run_startup_migrations()

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
