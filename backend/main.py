from fastapi import FastAPI
from app.api.routes import story, interaction
from app.core.memory.session_manager import create_tables
import logging
from contextlib import asynccontextmanager

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating tables...")
    create_tables()
    logger.info("Tables created successfully.")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.include_router(story.router, prefix="/story", tags=["story"])
app.include_router(interaction.router, prefix="/interaction", tags=["interaction"])

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    logger.info("Server started successfully.")
