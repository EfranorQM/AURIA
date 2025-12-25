from fastapi import FastAPI
from src.api.routers.categories import router as categories_router
from src.api.routers.black_market import router as black_market_router

app = FastAPI(title="AURIA API", version="0.1.0")

app.include_router(categories_router)
app.include_router(black_market_router)
