from fastapi import APIRouter, File, UploadFile
from fastapi_versioning import version

from app.services.palette_extraction import extract_colors

router = APIRouter(
    prefix="/palette",
    tags=["palette"],
    responses={404: {"description": "Not found"}},
)

@version(1)
@router.post('/{color_count}')
async def extract_palette(color_count: int, image: UploadFile = File(...)):
    img = await image.read()
    colors = extract_colors(img, color_count)
    return { "palette": colors }