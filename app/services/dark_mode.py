from typing import List
from app.services.color_generation import hsl_to_rgb, rgb_to_hsl, hex_to_rgb, luminance, find_contrast, check_contrast

Dark_palette = List[int]

def generate_dark_palette(palette: list) -> Dark_palette:
    hsl_palette = []
    rgb_palette = []
    print(palette)
    try:
        for index, color in zip(range(4), palette):
            if index < 4:
                rgb_color = hex_to_rgb(color)
                hsl_color = rgb_to_hsl(rgb_color)
                hsl_palette.append(hsl_color)
        
        for color in hsl_palette:
            color = list(color)
            # adjust saturation and luminance for pastel color
            color[1] = 100
            color[2] = 80
            rgb_color = hsl_to_rgb(color)
            rgb_palette.append(rgb_color)

        return rgb_palette
    except:
        return False