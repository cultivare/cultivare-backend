from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import db
from app.config import settings
from app.routers import cultures, notes, tags, search, stats, labelprint
from app.db_example.empty_db_init import init_db

# --- MongoDB lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # run on start
    try:
        await init_db()
    except Exception as e:
        print(f"Error init empty db: {e}")
    
    try:
        print("Creating indexes...")
        # Create indexes (using await)
        await db.cultures_collection.create_index("slug", unique=True)
        await db.cultures_collection.create_index("id", unique=True)
        await db.notes_collection.create_index("id", unique=True)
        
        await db.cultures_collection.create_index([("tags", "text"), ("name", "text")])
        await db.notes_collection.create_index([("tags", "text"), ("text", "text")])
        
        print("Indexes created successfully!")
        yield
        # run on shutdown
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        print("Closing MongoDB connection...")
        db.client.close()
        print("MongoDB connection closed.")


app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# --- CORS Configuration ---
# Allow requests from a frontend running on designated port
origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Mount the uploads directory as a static files directory
app.mount("/api/static", StaticFiles(directory=settings.MEDIA_DIR), name="static")

# Routers
api_router = APIRouter(prefix="/api")  # Main API router
api_router.include_router(cultures.router)
api_router.include_router(notes.router)
api_router.include_router(tags.router)
api_router.include_router(search.router)
api_router.include_router(stats.router)
api_router.include_router(labelprint.router)
app.include_router(api_router)  # Include the main router
