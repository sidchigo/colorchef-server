import random, time
import pandas as pd
import numpy as np
from typing import List, Callable, Tuple
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)

RGB_list = List[int]
RGB_color = Tuple[int]

parser = reqparse.RequestParser()
parser.add_argument('hex_color', action='append')
parser.add_argument('scale')

class Colors(Resource):

    def generate_colors(self, color: tuple) -> list:
        # if color == '':
        #     color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        Bcolor = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return [color, Bcolor()]

    # generate n no of random colors
    def generate_n_colors(self, size: int) -> RGB_list:
        color = lambda : (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return [color() for _ in range(size)]

    # hex to rgb converter
    def hex_to_rgb(self, color: str) -> RGB_color:
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    # luminance generator
    def luminance(self, rgb: list) -> list:
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
    def find_contrast(self, colors: list) -> float:
        if colors[0] > colors[1]:
            ratio = (colors[1] + 0.05) / (colors[0] + 0.05)
        else:
            ratio = (colors[0] + 0.05) / (colors[1] + 0.05)
        
        return ratio

    # classify ratio on scale
    def check_contrast(self, color: float) -> list:
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

    # find fit colors matching the given scale
    def fitness_func(self, selected_color: RGB_color, input_colors: RGB_list, scale: int) -> list:
        colors = []
        for color in input_colors:
            color_pair = [selected_color, color]
            luminance_pair = self.luminance(color_pair)
            contrast = self.find_contrast(luminance_pair)
            result = self.check_contrast(contrast)

            if result[int(scale) - 1] == True:
                colors.append('#' + '%02x%02x%02x' % color)

        return colors

    # api to get fit colors
    def get(self):
        args = parser.parse_args()
        fit_colors = []
        for color in args.hex_color:
            rgb_color = self.hex_to_rgb(color)
            color_list = self.generate_n_colors(1000)
            fit_colors.append(self.fitness_func(rgb_color, color_list, args.scale))
        
        return { 'colors': fit_colors }, 201

# routes
api.add_resource(Colors, '/colors')

if __name__ == '__main__':
    app.run(debug=True)