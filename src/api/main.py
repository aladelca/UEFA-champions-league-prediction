from fastapi import FastAPI

from src.api.routers import router


app = FastAPI(
    title="UCL Champion Predictor API",
    version="v1",
    description="Local preseason inference API for match probabilities and champion simulation.",
)
app.include_router(router)
