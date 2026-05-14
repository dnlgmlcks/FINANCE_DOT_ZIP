import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.report_api import router as report_router

app = FastAPI(
    title="Finance DOT ZIP API",
    description="재무 데이터 분석 및 Warning Signal API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    report_router,
    prefix="/api/v1",
    tags=["report"]
)


@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "Finance DOT ZIP API is running"
    }
