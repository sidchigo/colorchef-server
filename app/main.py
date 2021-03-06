from fastapi import FastAPI
from fastapi_versioning import VersionedFastAPI, version
from starlette.middleware.cors import CORSMiddleware

from .routers import palette

app = FastAPI(title="Colorchef")

origins = ['*']

app.include_router(palette.router)

@version(1)
@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}')
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)