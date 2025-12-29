from app.schemas.cinema import MovieListRequest
from app.services.cinema_service import process_movies_background, soft_delete_movie, hard_delete_movie
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi_versioning import version

import json
import logging
import os

from app.constants import (
    MOVIES_DIR,
    INDEX_FILE,
    CONFIG_FILE
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
@router.patch("/{slug}/archive")
async def archive_movie(slug: str):
    """
    Soft Delete: Hides the movie from the frontend but keeps the data file in the repo.
    """
    success = soft_delete_movie(slug)
    
    if not success:
        # 404 is appropriate because if the file doesn't exist, we can't archive it
        raise HTTPException(
            status_code=404, 
            detail=f"Movie '{slug}' not found or could not be archived"
        )
        
    return {"message": f"Movie '{slug}' successfully archived (hidden from public)."}

@version(1)
@router.delete("/{slug}/permanent")
async def delete_movie_permanently(slug: str):
    """
    Hard Delete: Physically removes the JSON file from the server/repo.
    This action is irreversible.
    """
    success = hard_delete_movie(slug)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Movie '{slug}' not found or could not be deleted"
        )
        
    return {"message": f"Movie '{slug}' permanently deleted."}

@router.get('/config')
async def get_local_config():
    if not os.path.exists(CONFIG_FILE): return {}
    with open(CONFIG_FILE, 'r') as f: return json.load(f)

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

@version(1)
@router.get('/{slug}') 
async def get_movie_detail(slug: str):
    """
    Fetches a single movie JSON file.
    Used by Next.js [slug].tsx during local development.
    """
    try:
        file_path = os.path.join(MOVIES_DIR, f"{slug}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404)
        
        with open(file_path, 'r') as f: return json.load(f)
    except Exception as e:  
        logger.error(f"Error fetching cinema index: {e}")
        raise HTTPException(status_code=500, detail=str(e))