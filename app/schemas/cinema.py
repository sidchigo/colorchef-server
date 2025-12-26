from pydantic import BaseModel

from typing import List, Optional

class MovieRequest(BaseModel):
    title: str
    year: Optional[int] = None
    region: Optional[str] = None

class MovieListRequest(BaseModel):
    movies: List[MovieRequest]
    tmdb_api_key: str