import random, time
import pandas as pd
import numpy as np
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)

class Colors(Resource):

    def generate_colors(color: tuple) -> list:
        # if color == '':
        #     color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        Bcolor = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return [color, Bcolor()]

    # generate n no of random colors
    def generate_n_colors(size: int) -> list:
        color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return [color() for _ in range(size)]

    # hex to rgb converter
    def hex_to_rgb(color: str) -> tuple:
        # print(colorlist[1])
        # hex1 = colorlist[0].lstrip('#')
        # hex2 = colorlist[1].lstrip('#')
        # print(tuple(int(hex2[i:i+2], 16) for i in (0, 2, 4)))
        # foreground = tuple(int(hex1[i:i+2], 16) for i in (0, 2, 4))
        # background = tuple(int(hex2[i:i+2], 16) for i in (0, 2, 4))
        # return [foreground, background]
        color = color.lstrip('#')
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

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

def find_contrast(colors: list) -> float:
    if colors[0] > colors[1]:
        ratio = (colors[1] + 0.05) / (colors[0] + 0.05)
    else:
        ratio = (colors[0] + 0.05) / (colors[1] + 0.05)
    
    return ratio

def check_contrast(color: float) -> list:
    passing_test = []
    # good
    if color < (1/4.5):
        passing_test.append(True)
    else:
        passing_test.append(False)

    # very good
    if color < (1/7):
        passing_test.append(True)
    else:
        passing_test.append(False)
    
    # super
    if color < (1/10):
        passing_test.append(True)
    else:
        passing_test.append(False)

    # ultimate
    if color < (1/13):
        passing_test.append(True)
    else:
        passing_test.append(False)
    
    return passing_test

# print(checkContrast(findContrast(luminance(hexToRGB(generateColors())))))

def fitness_func(selected_color: str, input_colors: list, scale: int) -> list:
    colors = []
    for color in input_colors:
        colorlist = [selected_color, color]
        luminanceList = luminance(colorlist)
        contrast = find_contrast(luminanceList)
        result = check_contrast(contrast)

        if result[scale - 1] == True:
            colors.append('#' + '%02x%02x%02x' % color)

    return colors

def fitness_func_old(selected_color: str, scale: int, limit: int) -> list:
    colors = []
    count = 0
    iterations = 0
    while count <= limit:
        iterations += 1
        colorlist = generate_colors(selected_color)
        luminanceList = luminance(colorlist)
        contrast = find_contrast(luminanceList)
        result = check_contrast(contrast)

        if result[scale - 1] == True:
            count += 1
            colors.append('#' + '%02x%02x%02x' % colorlist[1])

    print(f"Iterations: {iterations}")
    return colors


scale = 3
# selected_colors = ['#001219', '#ECE3D5', '#E9D8A6', '#EE9B00', '#314CB6', '#9B2226']
selected_colors = ['#FF1842', '#FFD3DB', '#E9D8A6', '#EE9B00', '#314CB6', '#9B2226']
rgbs = [hex_to_rgb(color) for color in selected_colors]
limit = 160
newstart = time.time()
fit_colors = []
fit_colors_old = []
for selected_color in rgbs:
    color_list = generate_n_colors(1000)
    fit_colors.append(fitness_func(selected_color, color_list, scale))
newend = time.time()
print(f"number of fit colors: {len(fit_colors[0])}")
print(f"time required new: {newend-newstart}")
print(fit_colors[1])

# oldstart = time.time()
# for selected_color in rgbs:
#     fit_colors_old.append(fitness_func_old(selected_color, scale, limit))
# oldend = time.time()
# print(f"number of fit colors: {len(fit_colors_old)}")
# print(f"time required old: {oldend-oldstart}")

# print(set(fit_colors))
# dataset = pd.DataFrame(fit_colors).transpose()
# print(dataset)
# dataset.columns = ['#001219', '#0A9396', '#E9D8A6', '#EE9B00', '#BB3E03', '#9B2226']
# dataset.index = pd.RangeIndex(len(dataset.index))
# dataset.to_csv('colors.csv', index=False, mode='a')