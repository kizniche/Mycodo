# -*- coding: utf-8 -*-
#
#  image.py - Mycodo image core utils
#
#  Copyright (C) 2015-2020 Kyle T. Gabriel <mycodo@kylegabriel.com>
#
#  This file is part of Mycodo
#
#  Mycodo is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mycodo is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mycodo. If not, see <http://www.gnu.org/licenses/>.
#
#  Contact at kylegabriel.com
import logging

logger = logging.getLogger("mycodo.utils.image")


def generate_thermal_image_from_pixels(
        pixels, nx, ny, path_file, rotate_ccw=270, scale=25, temp_min=None, temp_max=None):
    """Generate and save image from list of pixels."""
    from colour import Color
    from PIL import Image
    from PIL import ImageDraw

    if len(pixels) != nx * ny:
        logger.error("{nx} * {ny} does not equal {px}".format(
            nx=nx, ny=ny, px=len(pixels)))
        return

    # output image buffer
    image = Image.new("RGB", (nx, ny), "white")
    draw = ImageDraw.Draw(image)

    # color map
    COLORDEPTH = 256
    colors = list(Color("indigo").range_to(Color("red"), COLORDEPTH))
    colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

    # some utility functions
    def constrain(val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def map_it(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # map sensor readings to color map
    MINTEMP = min(pixels) if temp_min is None else temp_min
    MAXTEMP = max(pixels) if temp_max is None else temp_max
    pixels = [map_it(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]

    # create the image
    for ix in range(nx):
        for iy in range(ny):
            draw.point([(ix, iy % nx)], fill=colors[constrain(int(pixels[ix + nx * iy]), 0, COLORDEPTH - 1)])

    if rotate_ccw:
        image = image.rotate(rotate_ccw)

    # scale and save
    image.resize((nx * scale, ny * scale), Image.BICUBIC).save(path_file)
