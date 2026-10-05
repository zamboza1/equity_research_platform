from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Vertige Research API", version="1.2.0")

@app.exception_handler(ValueError)
async def invalid_model(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail":str(exc)})

@app.get("/health")
@app.get("/api/status")
def health():
    return {"status": "ok", "version": "1.2.0",
            "data_mode": "offline" if os.getenv("VERTIGE_OFFLINE") == "1" else "provider",
            "fred_key_configured": bool(os.getenv("FRED_API_KEY", "").strip())}


# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3005",  # Custom frontend port
    "http://localhost:8000",
    "http://localhost:8005",  # Custom backend port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import valuation, market_data, macro, education

app.include_router(valuation.router, prefix="/api/valuation", tags=["Valuation"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])
app.include_router(macro.router, prefix="/api/macro", tags=["Macro Data"])
app.include_router(education.router, prefix="/api/education", tags=["Education"])
from app.routers import news
app.include_router(news.router, prefix="/api/news", tags=["News"])
from app.routers import comparables
app.include_router(comparables.router, prefix="/api/comparables", tags=["Comparables"])
from app.routers import stats
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
from app.routers import builder
app.include_router(builder.router, prefix="/api/builder", tags=["Model Builder"])
from app.routers import industries
app.include_router(industries.router, prefix="/api/industries", tags=["Industry Analysis"])
from app.routers import export
app.include_router(export.router, prefix="/api/export", tags=["Export"])
from app.routers import research
app.include_router(research.router, prefix="/api/research", tags=["Research"])

@app.get("/")
def read_root():
    return {"message": "Equity Research Platform API is running"}
