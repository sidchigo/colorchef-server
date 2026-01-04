from typing import List, Optional
from app.schemas.cinema import MovieRequest
from app.services.palette_extraction import extract_colors
from datetime import datetime
from app.constants import (
    CONFIG_FILE,
    TMDB_SEARCH_URL,
    TMDB_IMAGES_URL,
    TMDB_IMAGE_BASE_URL,
    MOVIES_DIR,
    INDEX_FILE
)

import httpx
import requests
import logging
import json
import os

logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

def generate_slug(title: str) -> str:
    """Convert movie title to URL-friendly slug"""
    return (
        title.lower()
        .replace(' ', '-')
        .replace(':', '')
        .replace("'", '')
        .replace('"', '')
        .replace('&', 'and')
    )

async def extract_palette_from_url(url: str) -> List[str]:
    """Fetch image from URL and extract color palette"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            return extract_colors(response.content)
    return []

async def get_movie_keywords(movie_id: int, api_key: str) -> List[str]:
    """Fetch raw plot keywords from TMDB"""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"api_key": api_key})
        if response.status_code == 200:
            keywords_data = response.json()
            return [k['name'] for k in keywords_data.get('keywords', [])]
    return []

def load_config():
    """Load niche_map and other settings from config.json"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("niche_map", {})
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")
    
    # Fallback to empty dict or your hardcoded defaults
    return {}

def map_niche_tags(raw_keywords: List[str]) -> List[str]:
    """
    Map broad TMDB keywords to your specific 'Niche Tags'.
    Handles both string and list values in niche_map.
    """
    niche_map = load_config()
    found_tags = set()
    for kw in raw_keywords:
        kw_lower = kw.lower()
        if kw_lower in niche_map:
            val = niche_map[kw_lower]
            if isinstance(val, list):
                found_tags.update(val)
            else:
                found_tags.add(val)
            
    return list(set(found_tags))

async def get_watch_providers(movie_id: int, api_key: str, country_code="US"):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers"
    params = {"api_key": api_key}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        
    # Get providers for the specific country (e.g., US or IN)
    country_data = data.get("results", {}).get(country_code, {})
    
    # Return just the flatrate (streaming) providers
    # e.g. [{'provider_name': 'Netflix', 'logo_path': '/...jpg'}, ...]
    return country_data.get("flatrate", [])

# --- CORE DATA MANAGEMENT ---

def save_movie_file(movie_data: dict, slug: str) -> bool:
    """
    Save individual movie data to [slug].json file.
    PRESERVES existing 'is_visible' status if not provided in update.
    """
    try:
        movie_file = os.path.join(MOVIES_DIR, f'{slug}.json')
        
        # Check for existing data to preserve visibility state
        existing_visibility = True
        if os.path.exists(movie_file):
            try:
                with open(movie_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_visibility = existing_data.get('is_visible', True)
            except Exception:
                pass # If file is corrupt, default to True

        # Use provided is_visible or fall back to existing
        is_visible = movie_data.get('is_visible', existing_visibility)

        movie_with_metadata = {
            **movie_data,
            'slug': slug,
            'is_visible': is_visible,
            'updated_at': datetime.now().isoformat()
        }
        
        # Ensure directory exists
        if not os.path.exists(MOVIES_DIR):
            os.makedirs(MOVIES_DIR)

        with open(movie_file, 'w', encoding='utf-8') as f:
            json.dump(movie_with_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved movie: {slug}")
        return True
    except Exception as e:
        logger.error(f"Error saving movie {slug}: {str(e)}")
        return False

def rebuild_index() -> bool:
    """
    Scans ALL .json files in the movies directory to rebuild index.json.
    - If 'is_visible' is False, it excludes the movie from the index.
    - This handles 'Soft Deletion' correctly.
    """
    try:
        index_data = []
        if not os.path.exists(MOVIES_DIR):
            os.makedirs(MOVIES_DIR)

        # List all JSON files
        files = [f for f in os.listdir(MOVIES_DIR) if f.endswith('.json')]
        
        for filename in files:
            file_path = os.path.join(MOVIES_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    movie = json.load(f)
                
                if movie.get('is_visible', True):
                    index_entry = {
                        'title': movie.get('title'),
                        'slug': movie.get('slug'),
                        'palette': movie.get('palette', []),
                        'backdrop_url': movie.get('backdrop_url'),
                        'tags': movie.get('tags', []),
                        "raw_keywords": movie.get('raw_keywords', []),
                    }
                    index_data.append(index_entry)
            except Exception as e:
                logger.error(f"Skipping corrupt file {filename}: {e}")

        # Save the master index
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Rebuilt index with {len(index_data)} visible movies")
        return True
    except Exception as e:
        logger.error(f"Error rebuilding index: {str(e)}")
        return False

# --- SYNC & DELETE OPERATIONS ---

def sync_cinema_data(movies_data: list) -> dict:
    """
    Additive Sync: Saves provided movies, then REBUILDS index from disk.
    Does NOT delete missing movies.
    """
    report = {
        'success': True,
        'saved_movies': 0,
        'failed_movies': 0,
        'index_updated': False,
        'revalidation_triggered': False,
        'errors': []
    }
    
    logger.info("Starting Cinema Data Sync")
    
    # Step 1: Save individual movie files
    for movie in movies_data:
        slug = movie.get('slug') or generate_slug(movie.get('title', ''))
        if save_movie_file(movie, slug):
            report['saved_movies'] += 1
        else:
            report['failed_movies'] += 1
            report['success'] = False
            report['errors'].append(f"Failed to save movie: {slug}")
    
    # Step 2: Rebuild index from disk (Includes all existing + new movies)
    if rebuild_index():
        report['index_updated'] = True
    else:
        report['success'] = False
        report['errors'].append("Failed to rebuild index file")
    
    return report

def soft_delete_movie(slug: str) -> bool:
    """
    Soft Delete: Sets 'is_visible': False & rebuilds index.
    File remains in repo.
    """
    file_path = os.path.join(MOVIES_DIR, f"{slug}.json")
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data['is_visible'] = False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        rebuild_index()
        return True
    except Exception as e:
        logger.error(f"Soft delete failed for {slug}: {e}")
        return False

def hard_delete_movie(slug: str) -> bool:
    """Hard Delete: Physically removes file."""
    file_path = os.path.join(MOVIES_DIR, f"{slug}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            rebuild_index()
            return True
        except Exception as e:
            logger.error(f"Hard delete failed: {e}")
            return False
    return False


async def process_movies_background(movies: List[MovieRequest], tmdb_api_key: str):
    """Background task to fetch backdrops, extract palettes, and tag"""
    movies_data = []
    
    logger.info(f"Starting to process {len(movies)} movies")
    
    for movie_req in movies:
        title = movie_req.title
        year = movie_req.year
        region = movie_req.region
        curated_tags = movie_req.tags
        logger.info(curated_tags)
        try:
            async with httpx.AsyncClient() as client:
                # Build search params
                search_params = {"api_key": tmdb_api_key, "query": title}
                if year: search_params["year"] = year
                if region: search_params["region"] = region
                
                search_response = await client.get(TMDB_SEARCH_URL, params=search_params)
                search_data = search_response.json()
                
                if search_data.get("results"):
                    movie = search_data["results"][0]
                    movie_id = movie.get("id")
                    movie_title = movie.get("title")
                    movie_year = movie.get("release_date")[0:4]

                    # Keywords & Niche Tags
                    raw_keywords = await get_movie_keywords(movie_id, tmdb_api_key)
                    niche_tags = map_niche_tags(raw_keywords)

                    # combining both lists and de-duplicating tags
                    final_tags = list(dict.fromkeys([t.lower() for t in (curated_tags + niche_tags)]))
                    
                    # Fill gaps with raw keywords
                    for kw in raw_keywords:
                        formatted_kw = kw.lower()
                        
                        if formatted_kw not in final_tags:
                            final_tags.append(formatted_kw)
                            
                        # Stop once we have enough tags for the UI (e.g., 6 tags max)
                        if len(final_tags) >= 6:
                            break
                    
                    # Images
                    images_response = await client.get(
                        TMDB_IMAGES_URL.format(movie_id=movie_id),
                        params={"api_key": tmdb_api_key}
                    )
                    images_data = images_response.json()
                    backdrops = images_data.get("backdrops", [])
                    
                    # Sort backdrops by vote count
                    best_backdrops = sorted(
                        backdrops[:3], 
                        key=lambda x: x.get("vote_count", 0), 
                        reverse=True
                    )
                    
                    providers = await get_watch_providers(movie_id, tmdb_api_key)
                    if best_backdrops:
                        best_backdrop = best_backdrops[0]
                        backdrop_path = best_backdrop.get("file_path")
                        
                        if backdrop_path:
                            backdrop_url = f"{TMDB_IMAGE_BASE_URL}{backdrop_path}"
                            palette = await extract_palette_from_url(backdrop_url)
                            slug = generate_slug(title)
                            
                            movie_data = {
                                "title": movie_title,
                                "year": movie_year,
                                "tmdb_id": movie_id,
                                "palette": palette,
                                "backdrop_url": backdrop_url,
                                "slug": generate_slug(movie_title + "_" + movie_year),
                                "tags": final_tags,
                                "providers": providers,
                                "raw_keywords": raw_keywords[:10],
                                "is_visible": True
                            }
                            movies_data.append(movie_data)
        except Exception as e:
            logger.error(f"Error processing {title}: {e}", exc_info=True)
    
    # Sync the collected movies data using the new Additive Sync
    if movies_data:
        sync_cinema_data(movies_data)
    else:
        logger.warning("No movies were successfully processed")