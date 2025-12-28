from pydantic import BaseModel

from typing import List, Optional

class MovieRequest(BaseModel):
    title: str
    is_visible: bool = True
    year: Optional[int] = None
    region: Optional[str] = None
    tags: Optional[List[str]] = []

class MovieListRequest(BaseModel):
    movies: List[MovieRequest]
    tmdb_api_key: str