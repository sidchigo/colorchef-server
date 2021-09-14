from typing import List
from app.services.color_generation import hsl_to_rgb, rgb_to_hsl, hex_to_rgb, luminance, find_contrast

Dark_palette = List[int]

def generate_dark_palette(palette: list) -> Dark_palette:
    hsl_palette = []
    rgb_palette = []
    try:
        for color in palette:
            rgb_color = hex_to_rgb(color)
            hsl_color = rgb_to_hsl(rgb_color)
            hsl_palette.append(hsl_color)
        
        for color in hsl_palette:
            # adjust saturation
            if color[1] < 80:
                color[1] = 100
            
            # adjust luminance
            if color[2] < 50:
                color[2] = color[2] + 10
            rgb_color = hsl_to_rgb(color)
            rgb_palette.append(rgb_color)
        
        print(rgb_palette)
        luminance_pair = luminance(rgb_palette)
        contrast_ratio = find_contrast(luminance_pair)
        print(contrast_ratio)
        return hsl_palette
    except:
        return False