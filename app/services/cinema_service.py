from typing import List, Optional
from app.schemas.cinema import MovieRequest
from app.services.palette_extraction import extract_colors
from datetime import datetime
from app.constants import (
    TMDB_SEARCH_URL,
    TMDB_IMAGES_URL,
    TMDB_IMAGE_BASE_URL,
    DATA_REPO_PATH,
    MOVIES_DIR,
    INDEX_FILE,
    REVALIDATE_SECRET,
    REVALIDATE_URL,
)

import httpx
import subprocess
import requests
import logging
import json
import os

logger = logging.getLogger(__name__)

niche_map = {
    "shamanism": ["Shamanism", "Religious Horror"],
    "shaman": ["Shamanism", "Religious Horror"],
    "exorcism": "Exorcism",
    "possession": "Possession",
    "found footage": "Found Footage",
    "folk horror": "Folk Horror",
    "curse": ["Curse", "Religious Horror"],
    "ritual": ["Ritual", "Religious Horror"]
}

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


def map_niche_tags(raw_keywords: List[str]) -> List[str]:
    """
    Map broad TMDB keywords to your specific 'Niche Tags'.
    You can expand this dictionary as you find more correlations.
    """
    found_tags = set()
    for kw in raw_keywords:
        kw_lower = kw.lower()
        if kw_lower in niche_map:
            val = niche_map[kw_lower]
            if isinstance(val, list):
                found_tags.update(val)
            else:
                found_tags.add(val)
            
    return list(found_tags)


def save_movie_file(movie_data: dict, slug: str) -> bool:
    """
    Save individual movie data to [slug].json file
    
    Args:
        movie_data: Dictionary containing movie information
        slug: URL-friendly slug for the movie
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        movie_file = os.path.join(MOVIES_DIR, f'{slug}.json')
        
        # Ensure movie data has required fields
        movie_with_metadata = {
            **movie_data,
            'slug': slug,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(movie_file, 'w', encoding='utf-8') as f:
            json.dump(movie_with_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved movie: {slug}")
        return True
    except Exception as e:
        logger.error(f"Error saving movie {slug}: {str(e)}")
        return False


def update_index(movies_data: list) -> bool:
    """
    Update root index.json with movie metadata for discovery grid
    
    Args:
        movies_data: List of movie dictionaries
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        index_data = []
        
        for movie in movies_data:
            slug = movie.get('slug') or generate_slug(movie.get('title', ''))
            
            index_entry = {
                'title': movie.get('title'),
                'slug': slug,
                'palette': movie.get('palette', []),
                'backdrop_url': movie.get('backdrop_url'),
                'tmdb_id': movie.get('tmdb_id'),
                'tags': movie.get('tags', '')
            }
            index_data.append(index_entry)
        
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated index.json with {len(index_data)} movies")
        return True
    except Exception as e:
        logger.error(f"Error updating index: {str(e)}")
        return False

    """
    Commit and push changes to remote Git repository
    
    Args:
        commit_message: Commit message for Git
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        original_dir = os.getcwd()
        os.chdir(DATA_REPO_PATH)
        
        # Check if there are changes
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if not status.stdout.strip():
            logger.info("No changes to commit")
            os.chdir(original_dir)
            return True
        
        # Add all changes
        subprocess.run(
            ['git', 'add', '.'],
            check=True,
            capture_output=True
        )
        logger.info("Git add completed")
        
        # Commit changes
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Committed: {commit_message}")
        
        # Push to remote
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Pushed to remote repository")
        os.chdir(original_dir)
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git error: {str(e)}")
        os.chdir(original_dir)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during git operations: {str(e)}")
        os.chdir(original_dir)
        return False


def trigger_revalidation(slug: Optional[str] = None) -> bool:
    """
    Trigger Next.js ISR revalidation for updated pages
    
    Args:
        slug: Optional specific slug to revalidate. If None, revalidates index
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if slug:
            path = f'/cinema/{slug}'
        else:
            path = '/cinema'
        
        params = {
            'secret': REVALIDATE_SECRET,
            'path': path
        }
        
        response = requests.get(REVALIDATE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Revalidated: {path}")
            return True
        else:
            logger.warning(f"Revalidation failed for {path}: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering revalidation: {str(e)}")
        return False


def sync_cinema_data(movies_data: list) -> dict:
    """
    Main sync function: Save movies, update index, commit, and revalidate
    
    Args:
        movies_data: List of movie dictionaries to sync
    
    Returns:
        dict: Status report of the sync process
    """
    report = {
        'success': True,
        'saved_movies': 0,
        'failed_movies': 0,
        'index_updated': False,
        'git_pushed': False,
        'revalidation_triggered': False,
        'errors': []
    }
    
    logger.info("="*50)
    logger.info("Starting Cinema Data Sync")
    logger.info("="*50)
    
    # Step 1: Save individual movie files
    logger.info("Step 1: Saving movie files...")
    for movie in movies_data:
        slug = movie.get('slug') or generate_slug(movie.get('title', ''))
        if save_movie_file(movie, slug):
            report['saved_movies'] += 1
        else:
            report['failed_movies'] += 1
            report['success'] = False
            report['errors'].append(f"Failed to save movie: {slug}")
    
    # Step 2: Update index file
    logger.info("Step 2: Updating index file...")
    if update_index(movies_data):
        report['index_updated'] = True
    else:
        report['success'] = False
        report['errors'].append("Failed to update index file")
    
    # Step 3: Trigger revalidation
    logger.info("Step 3: Triggering Next.js revalidation...")
    if report['saved_movies'] > 0:
        if trigger_revalidation():
            report['revalidation_triggered'] = True
        else:
            report['errors'].append("Failed to trigger revalidation")
    
    logger.info("="*50)
    logger.info("Sync Complete")
    logger.info("="*50)
    
    return report


async def process_movies_background(movies: List[MovieRequest], tmdb_api_key: str):
    """Background task to fetch backdrops and extract color palettes"""
    movies_data = []
    
    logger.info(f"Starting to process {len(movies)} movies")
    
    for movie_req in movies:
        title = movie_req.title
        year = movie_req.year
        region = movie_req.region
        try:
            # Fetch movie data from TMDB
            async with httpx.AsyncClient() as client:
                # Build search params
                search_params = {"api_key": tmdb_api_key, "query": title}
                if year:
                    search_params["year"] = year
                if region:
                    search_params["region"] = region
                
                # Search for the movie
                search_response = await client.get(
                    TMDB_SEARCH_URL,
                    params=search_params
                )
                search_data = search_response.json()
                
                if search_data.get("results"):
                    movie = search_data["results"][0]
                    movie_id = movie.get("id")

                    raw_keywords = await get_movie_keywords(movie_id, tmdb_api_key)
                    niche_tags = map_niche_tags(raw_keywords)
                    
                    # Fetch images for the movie
                    images_response = await client.get(
                        TMDB_IMAGES_URL.format(movie_id=movie_id),
                        params={"api_key": tmdb_api_key}
                    )
                    images_data = images_response.json()
                    backdrops = images_data.get("backdrops", [])
                    
                    # Get the first 3 backdrops (sorted by rating/vote_count)
                    best_backdrops = sorted(
                        backdrops[:3], 
                        key=lambda x: x.get("vote_count", 0), 
                        reverse=True
                    )
                    
                    if best_backdrops:
                        best_backdrop = best_backdrops[0]
                        backdrop_path = best_backdrop.get("file_path")
                        
                        if backdrop_path:
                            backdrop_url = f"{TMDB_IMAGE_BASE_URL}{backdrop_path}"
                            palette = await extract_palette_from_url(backdrop_url)
                            
                            slug = generate_slug(title)
                            movie_data = {
                                "title": title,
                                "tmdb_id": movie_id,
                                "palette": palette,
                                "backdrop_url": backdrop_url,
                                "slug": slug,
                                "tags": niche_tags,
                                "raw_keywords": raw_keywords[:10]
                            }
                            movies_data.append(movie_data)
                        else:
                            logger.warning(f"No backdrop path found for {title}")
                    else:
                        logger.warning(f"No backdrops found for {title}")
                else:
                    logger.warning(f"No search results found for {title}")
        except Exception as e:
            logger.error(f"Error processing {title}: {e}", exc_info=True)
    
    # Sync the collected movies data
    if movies_data:
        sync_cinema_data(movies_data)
    else:
        logger.warning("No movies were successfully processed")
