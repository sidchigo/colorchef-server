import math, random, colorsys
from typing import List, Tuple

RGB_list = List[int]
RGB_color = Tuple[int]
HSL_color = Tuple[int]
HSB_color = Tuple[int]

def generate_colors(color: tuple) -> list:
    Bcolor = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return [color, Bcolor()]

# generate n no of random colors
def generate_n_colors(size: int) -> RGB_list:
    color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    return [color() for _ in range(size)]

# hex to rgb converter
def hex_to_rgb(color: str) -> RGB_color:
    color = color.lstrip('#')
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

# hsl to rgb converter
def hsl_to_rgb(hsl: list) -> RGB_color:
    hue = int(hsl[0])/360
    sat = int(hsl[1])/100
    lum = int(hsl[2])/100

    red = math.ceil(colorsys.hls_to_rgb(hue, lum, sat)[0] * 255)
    green = math.ceil(colorsys.hls_to_rgb(hue, lum, sat)[1] * 255)
    blue = math.ceil(colorsys.hls_to_rgb(hue, lum, sat)[2] * 255)

    return (red, green, blue)

# rgb to hsl converter
def rgb_to_hsl(rgb: list) -> HSL_color:
    red = int(rgb[0])/255
    green = int(rgb[1])/255
    blue = int(rgb[2])/255

    hue = math.ceil(colorsys.rgb_to_hls(red, green, blue)[0] * 360)
    lum = math.ceil(colorsys.rgb_to_hls(red, green, blue)[1] * 100)
    sat = math.ceil(colorsys.rgb_to_hls(red, green, blue)[2] * 100)

    return (hue, sat, lum)

# hsb to rgb converter
def hsb_to_rgb(hsb: list) -> RGB_color:
    hue = int(hsb[0])/360
    sat = int(hsb[1])/100
    brightness = int(hsb[2])/100

    red = math.ceil(colorsys.hsv_to_rgb(hue, sat, brightness)[0] * 255)
    green = math.ceil(colorsys.hsv_to_rgb(hue, sat, brightness)[1] * 255)
    blue = math.ceil(colorsys.hsv_to_rgb(hue, sat, brightness)[2] * 255)

    return (red, green, blue)

# rgb to hsb converter
def rgb_to_hsb(rgb: list) -> HSB_color:
    red = int(rgb[0])/255
    green = int(rgb[1])/255
    blue = int(rgb[2])/255

    hue = math.ceil(colorsys.rgb_to_hsv(red, green, blue)[0] * 360)
    sat = math.ceil(colorsys.rgb_to_hsv(red, green, blue)[1] * 100)
    brightness = math.ceil(colorsys.rgb_to_hsv(red, green, blue)[2] * 100)

    return (hue, sat, brightness)

# luminance generator
def luminance(rgb: list) -> list:
    foreground = []
    background = []

    for color in rgb[0]:
        color = color / 255
        if color <= 0.03928:
            color = color / 12.92
        else:
            color = pow(((color + 0.055) / 1.055), 2.4)
        foreground.append(color)
    
    color1 = foreground[0] * 0.2126 + foreground[1] * 0.7152 + foreground[2] * 0.0722

    for color in rgb[1]:
        color = color / 255
        if color <= 0.03928:
            color = color / 12.92
        else:
            color = pow(((color + 0.055) / 1.055), 2.4)
        background.append(color)
    
    color2 = background[0] * 0.2126 + background[1] * 0.7152 + background[2] * 0.0722

    return [color1, color2]

# calculate contrast ratio
def find_contrast(colors: list) -> float:
    if colors[0] > colors[1]:
        ratio = (colors[1] + 0.05) / (colors[0] + 0.05)
    else:
        ratio = (colors[0] + 0.05) / (colors[1] + 0.05)
    
    return ratio

# classify ratio on scale
def check_contrast(color: float, luminance: float) -> list:
    passing_test = []
    contrast_params = []

    if luminance < 0.025 or luminance > 0.7:
        contrast_params = [7, 8, 10, 12]
    else:
        contrast_params = [6, 7, 8, 9]

    # good
    if color < (1/contrast_params[0]):
        passing_test.append(True)
    else:
        passing_test.append(False)

    # very good
    if color < (1/contrast_params[1]):
        passing_test.append(True)
    else:
        passing_test.append(False)
    
    # super
    if color < (1/contrast_params[2]):
        passing_test.append(True)
    else:
        passing_test.append(False)

    # ultimate
    if color < (1/contrast_params[3]):
        passing_test.append(True)
    else:
        passing_test.append(False)
    
    return passing_test

# find fit colors matching the given scale
def fitness_func(selected_color: RGB_color, input_colors: RGB_list, scale: int) -> list:
    colors = []
    for color in input_colors:
        color_pair = [selected_color, color]
        luminance_pair = luminance(color_pair)
        luminance_factor = luminance_pair[0]
        contrast = find_contrast(luminance_pair)
        result = check_contrast(contrast, luminance_factor)

        if result[int(scale) - 1] == True and len(colors) < 12:
            hex_color = '#' + '%02x%02x%02x' % color
            rgb_color = hex_to_rgb(hex_color)
            hsl_color = rgb_to_hsl(rgb_color)
            hsb_color = rgb_to_hsb(rgb_color)
            colors.append({ 
                "hex": hex_color,
                "rgb": rgb_color,
                "hsl": hsl_color,
                "hsb": hsb_color
            })

    return colors