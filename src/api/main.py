from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.categories import router as categories_router
from src.api.routers.black_market import router as black_market_router

app = FastAPI(title="AURIA API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://auriapro.netlify.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)
app.include_router(black_market_router)
