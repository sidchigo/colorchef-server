from fastapi import APIRouter, HTTPException
from fastapi_versioning import version
from pydantic import BaseModel
from app.services.dark_mode import generate_dark_palette

class Palette(BaseModel):
    palette: list

router = APIRouter(
    prefix="/dark",
    tags=["dark mode"],
    responses={404: {"description": "Palette not found"}},
)

@version(1)
@router.post('/')
async def get_dark_palette(hex_palette: Palette):
    try:
        dark_palette = generate_dark_palette(hex_palette.palette)
        
        if dark_palette:
            return { "dark_palette": dark_palette, "message": "Dark palette generated successfully." }
        else:
            raise HTTPException(
                status_code=404, detail="Invalid colors provided"
            )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=404, detail="Palette not generated"
        )
    