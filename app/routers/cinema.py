from app.schemas.cinema import MovieListRequest
from app.services.cinema_service import process_movies_background
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi_versioning import version

import json
import logging
import os

from app.constants import (
    MOVIES_DIR,
    INDEX_FILE,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/cinema",
    tags=["cinema"],
    responses={404: {"description": "Not found"}},
)

@version(1)
@router.post('/sync')
async def sync_cinema_palettes(request: MovieListRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to extract color palettes from movie backdrops and sync to Git
    
    Body params:
    - movies: List of movie objects with title, year (optional), region (optional)
    - tmdb_api_key: Your TMDB API key
    
    Process:
    1. Fetches movie data from TMDB
    2. Saves individual movie files to movies/ directory
    3. Updates root index.json
    4. Commits and pushes to Git repository
    5. Triggers Next.js ISR revalidation
    """
    background_tasks.add_task(process_movies_background, request.movies, request.tmdb_api_key)
    
    return {
        "status": "processing",
        "message": f"Started processing {len(request.movies)} movies",
        "details": "Changes will be synced to Git and revalidated on Next.js"
    }


@version(1)
@router.get('/data')
async def get_cinema_data():
    """
    Endpoint to retrieve all cinema data from individual movie files
    Returns data in the format expected by Next.js
    """
    try:
        cinema_data = {}
        
        if not os.path.exists(MOVIES_DIR):
            return cinema_data
        
        for filename in os.listdir(MOVIES_DIR):
            if filename.endswith('.json'):
                slug = filename[:-5]  # Remove .json extension
                filepath = os.path.join(MOVIES_DIR, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    movie_data = json.load(f)
                    cinema_data[slug] = movie_data
        
        return cinema_data
    except Exception as e:
        logger.error(f"Error fetching cinema data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@version(1)
@router.get('/index')
async def get_cinema_index():
    """
    Endpoint to retrieve the index file for the discovery grid
    Contains only essential metadata for performance
    """
    try:
        if not os.path.exists(INDEX_FILE):
            return []
        
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        return index_data
    except Exception as e:
        logger.error(f"Error fetching cinema index: {e}")
        raise HTTPException(status_code=500, detail=str(e))
