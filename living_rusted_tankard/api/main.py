"""FastAPI application for The Living Rusted Tankard."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from core.db.session import engine, init_db
from .routers import sessions, game
from .deps import get_db

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Initialize the database
    SQLModel.metadata.create_all(bind=engine)
    
    app = FastAPI(
        title="The Living Rusted Tankard API",
        description="API for The Living Rusted Tankard text adventure game",
        version="0.1.0"
    )
    
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(sessions.router, prefix="/api", tags=["sessions"])
    app.include_router(game.router, prefix="/api", tags=["integrated-game"])
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}
    
    return app

# Create the FastAPI app
app = create_app()

# Initialize the database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
