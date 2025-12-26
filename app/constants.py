import os
from pathlib import Path

# TMDB API Configuration
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGES_URL = "https://api.themoviedb.org/3/movie/{movie_id}/images"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w1280"

# Cinema Data Repository Configuration
DATA_REPO_PATH = os.getenv('DATA_REPO_PATH', 'colorchef-data')
MOVIES_DIR = os.path.join(DATA_REPO_PATH, 'movies')
INDEX_FILE = os.path.join(DATA_REPO_PATH, 'index.json')

# Revalidation Configuration
REVALIDATE_SECRET = os.getenv('REVALIDATE_SECRET', 'your-secret-key')
REVALIDATE_URL = 'https://colorchef.vercel.app/api/revalidate'

# Ensure directories exist
Path(MOVIES_DIR).mkdir(parents=True, exist_ok=True)