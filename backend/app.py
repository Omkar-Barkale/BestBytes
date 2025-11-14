# api imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# router imports
from routers import movieRouter

app = FastAPI(
    title="BestBytes Movie Review API",
    description="Backend API",
    version="1.0.0",
)

