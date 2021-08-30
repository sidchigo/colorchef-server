from fastapi import APIRouter, HTTPException
from fastapi_versioning import version
from typing import Optional
from random import choice

from app.services.color_generation import hex_to_rgb, hsl_to_rgb, hsb_to_rgb, generate_n_colors, fitness_func

router = APIRouter(
    prefix="/colors",
    tags=["colors"],
    responses={404: {"description": "Not found"}},
)

@version(1)
@router.get('/')
async def random_colors():
    fit_colors = []
    default_colors = ['FFA987', '49306B', 'F1D302', 'A1E8CC', '23CE6B', '06D6A0', 'DFB2F4', '41EAD4', '251605', '78C0E0']
    color_list = generate_n_colors(1000)
    random_color = choice(default_colors)
    color = hex_to_rgb(random_color)
    fit_colors.append(fitness_func(color, color_list, 2))
    
    return { "input_color": random_color, "colors": fit_colors[0], 'totalColors': len(fit_colors[0]) }

@version(1)
@router.get('/{hex}/{scale}')
async def colors(hex: str, scale: int):
    fit_colors = []
    try: 
        color = hex_to_rgb(hex)
        color_list = generate_n_colors(1000)
        result = fitness_func(color, color_list, scale)
        print(result)
        fit_colors.append(result)
        return { "input_color": hex, "colors": fit_colors[0], 'totalColors': len(fit_colors[0]) }
    except:
        raise HTTPException(
            status_code=404, detail="Page not found."
        )