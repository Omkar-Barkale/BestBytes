from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import (
    movieRouter,
    reviewRouter,
    userRouter,
    adminRouter,
    listsRouter
)

app = FastAPI(
    title="BestBytes Movie Review API",
    description="Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movieRouter.router, prefix="/movies", tags=["Movies"])
app.include_router(reviewRouter.router, prefix="/reviews", tags=["Reviews"])
app.include_router(userRouter.router, prefix="/users", tags=["Users"])
app.include_router(adminRouter.router, prefix="/admin", tags=["Admin"])
app.include_router(listsRouter.router, prefix="/lists", tags=["Lists"])

@app.get("/")
def root():
    """endpoint working"""
    return {"message": "API running"}
