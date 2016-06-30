#!/usr/bin/env python3

""" A helper tool for tile set operations. """

import argparse

from PIL import Image, ImageDraw, ImageFont

LOOP_X = 1
LOOP_Y = 2
FONT_FN = "/usr/share/fonts/TTF/calibri.ttf"
FONT_SIZE = 24



def parse_command_line():
    parser = argparse.ArgumentParser(description = "A helper tool for tile set operations.")
    parser.add_argument(
        "-i", "--input", type=str, help="Input file name", required=True)
    parser.add_argument(
        "-d", "--dim", type=int, help="Tile dimension, in pixels (32 by default)", default=32)
    parser.add_argument(
        "output", type=str, metavar="OUTPUT", help="Output file name")

    return parser.parse_args()

def main():
    args = parse_command_line()
    dim = args.dim
    color = (255, 0, 0)

    src_img = Image.open(args.input)
    img = Image.new("RGBA", (src_img.size[0] + dim, src_img.size[1] + dim), color="white")
    img.paste(src_img, (dim, dim))
    (iw, ih) = img.size

    dc = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_FN, FONT_SIZE)

    def delimit_tiles(i, x, y, end_x, end_y):
        string = str(i - 1)
        (text_w, text_h) = font.getsize(string)

        text_x = x + dim / 2 - text_w / 2
        text_y = y + dim / 2 - text_h / 2

        dc.line([x, y, end_x, end_y], fill=color, width=1)
        dc.text((text_x, text_y), string, font=font, fill=color)

    for i in range(1, iw // dim):
        x = i * dim - 1
        y = 0
        end_x = x
        end_y = ih - 1

        delimit_tiles(i, x, y, end_x, end_y)

    for i in range(1, ih // dim):
        x = 0
        y = i * dim - 1
        end_x = iw - 1
        end_y = y

        delimit_tiles(i, x, y, end_x, end_y)

    img.save(args.output)

main()
