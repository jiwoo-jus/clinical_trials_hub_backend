import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import search_routes, paper_routes, chat_routes, utils_routes
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Create log directory and configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(log_dir, f"log_{current_time}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Redirect stdout and stderr to logger
class LoggerWriter:
    def __init__(self, level):
        self.level = level
    def write(self, message):
        if message.strip():
            self.level(message.strip())
    def flush(self):
        pass

sys.stdout = LoggerWriter(logger.info)
sys.stderr = LoggerWriter(logger.error)

app = FastAPI()

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "").split(",")  # Read from .env and split by comma
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(search_routes.router, prefix="/api/search")
app.include_router(paper_routes.router, prefix="/api/paper")
app.include_router(chat_routes.router, prefix="/api/chat")
app.include_router(utils_routes.router, prefix="/api/utils", tags=["utilities"])

@app.get("/test")
async def test_endpoint():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info(f"Test endpoint accessed at {current_time}")
    return {"message": "CORS works!"}

if __name__ == "__main__":
    import uvicorn
    from config import PORT
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
