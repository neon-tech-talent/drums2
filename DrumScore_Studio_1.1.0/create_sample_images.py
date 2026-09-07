# create_sample_images.py - Generate realistic Drum Sheet Music images for testing
import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('assets/sample_images', exist_ok=True)

def draw_x(draw, cx, cy, size=10, color='black', width=2):
    half = size / 2.0
    draw.line([(cx - half, cy - half), (cx + half, cy + half)], fill=color, width=width)
    draw.line([(cx - half, cy + half), (cx + half, cy - half)], fill=color, width=width)

def draw_oval(draw, cx, cy, rx=7, ry=5, color='black'):
    draw.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)], fill=color, outline=color)

def draw_stem(draw, cx, cy, is_up=True, height=35, color='black', width=2):
    x = cx + 6 if is_up else cx - 6
    y_end = cy - height if is_up else cy + height
    draw.line([(x, cy), (x, y_end)], fill=color, width=width)

def create_sample_rock_image(filepath):
    width, height = 900, 260
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    # Margins and Staff geometry
    staff_y = 120
    line_spacing = 16
    lines = [staff_y + i * line_spacing for i in range(5)] # 5 staff lines

    # Draw 5 horizontal staff lines
    x_start = 60
    x_end = 840
    for y in lines:
        draw.line([(x_start, y), (x_end, y)], fill='#222222', width=2)

    # Clef (two vertical parallel bars)
    draw.line([(x_start + 15, lines[0]), (x_start + 15, lines[4])], fill='#111111', width=3)
    draw.line([(x_start + 22, lines[0]), (x_start + 22, lines[4])], fill='#111111', width=3)

    # 4/4 Time Signature lines
    draw.line([(x_start + 35, lines[0]), (x_start + 45, lines[2])], fill='#222222', width=2)
    draw.line([(x_start + 45, lines[0]), (x_start + 45, lines[4])], fill='#222222', width=2)

    # Measure bars (2 measures)
    meas_w = (x_end - (x_start + 60)) / 2
    bar1 = int(x_start + 60)
    bar2 = int(bar1 + meas_w)
    bar3 = int(x_end)

    draw.line([(bar1, lines[0]), (bar1, lines[4])], fill='#222222', width=2)
    draw.line([(bar2, lines[0]), (bar2, lines[4])], fill='#222222', width=2)
    draw.line([(bar3, lines[0]), (bar3, lines[4])], fill='#222222', width=3)
    draw.line([(bar3 - 4, lines[0]), (bar3 - 4, lines[4])], fill='#222222', width=1)

    # Draw notes in Measure 1 (Standard Rock Beat)
    # Hi-hat: above line 0 (y = lines[0] - 8)
    # Snare: space 3 (y = lines[2] + 8)
    # Kick: space 1 (y = lines[3] + 8)
    hh_y = lines[0] - 8
    snare_y = lines[1] + 8
    kick_y = lines[3] + 8

    # 8 eighth-note steps in Measure 1
    step_w = meas_w / 8.0
    for i in range(8):
        nx = bar1 + (i + 0.5) * step_w
        # Hi-Hat
        draw_x(draw, nx, hh_y, size=11, width=2)
        draw_stem(draw, nx, hh_y, is_up=True, height=28)

        # Kick on 1 and 3 (i=0, 4)
        if i in (0, 4):
            draw_oval(draw, nx, kick_y)
            draw_stem(draw, nx, kick_y, is_up=False, height=26)

        # Snare on 2 and 4 (i=2, 6)
        if i in (2, 6):
            draw_oval(draw, nx, snare_y)
            draw_stem(draw, nx, snare_y, is_up=True, height=26)

    # Draw notes in Measure 2 (Groove with Kick variation on 3&)
    for i in range(8):
        nx = bar2 + (i + 0.5) * step_w
        draw_x(draw, nx, hh_y, size=11, width=2)
        draw_stem(draw, nx, hh_y, is_up=True, height=28)

        if i in (0, 4, 5): # Kick on 1, 3, 3&
            draw_oval(draw, nx, kick_y)
            draw_stem(draw, nx, kick_y, is_up=False, height=26)

        if i in (2, 6): # Snare on 2 and 4
            draw_oval(draw, nx, snare_y)
            draw_stem(draw, nx, snare_y, is_up=True, height=26)

    img.save(filepath, format='PNG')
    print(f"Generated sample drum sheet image: {filepath} ({os.path.getsize(filepath)} bytes)")

def create_sample_fill_image(filepath):
    width, height = 900, 260
    img = Image.new('RGB', (width, height), color='#ffffff')
    draw = ImageDraw.Draw(img)

    staff_y = 120
    line_spacing = 16
    lines = [staff_y + i * line_spacing for i in range(5)]

    x_start = 60
    x_end = 840
    for y in lines:
        draw.line([(x_start, y), (x_end, y)], fill='#222222', width=2)

    # Bar lines
    meas_w = (x_end - (x_start + 60)) / 2
    bar1 = int(x_start + 60)
    bar2 = int(bar1 + meas_w)
    bar3 = int(x_end)

    draw.line([(bar1, lines[0]), (bar1, lines[4])], fill='#222222', width=2)
    draw.line([(bar2, lines[0]), (bar2, lines[4])], fill='#222222', width=2)
    draw.line([(bar3, lines[0]), (bar3, lines[4])], fill='#222222', width=3)

    hh_y = lines[0] - 8
    tom_high_y = lines[0] + 8
    tom_mid_y = lines[1]
    snare_y = lines[1] + 8
    kick_y = lines[3] + 8
    tom_low_y = lines[2] + 8

    # Measure 1: Normal beat
    step_w = meas_w / 8.0
    for i in range(8):
        nx = bar1 + (i + 0.5) * step_w
        draw_x(draw, nx, hh_y, size=11, width=2)
        draw_stem(draw, nx, hh_y, is_up=True, height=28)
        if i in (0, 4):
            draw_oval(draw, nx, kick_y)
            draw_stem(draw, nx, kick_y, is_up=False, height=26)
        if i in (2, 6):
            draw_oval(draw, nx, snare_y)
            draw_stem(draw, nx, snare_y, is_up=True, height=26)

    # Measure 2: Tom Fill (Snare -> High Tom -> Mid Tom -> Low Tom)
    fill_step = meas_w / 8.0
    for i in range(8):
        nx = bar2 + (i + 0.5) * fill_step
        if i < 2:
            draw_oval(draw, nx, snare_y)
            draw_stem(draw, nx, snare_y, is_up=True, height=26)
        elif i < 4:
            draw_oval(draw, nx, tom_high_y)
            draw_stem(draw, nx, tom_high_y, is_up=True, height=26)
        elif i < 6:
            draw_oval(draw, nx, tom_mid_y)
            draw_stem(draw, nx, tom_mid_y, is_up=True, height=26)
        else:
            draw_oval(draw, nx, tom_low_y)
            draw_stem(draw, nx, tom_low_y, is_up=True, height=26)

    img.save(filepath, format='PNG')
    print(f"Generated sample drum fill image: {filepath} ({os.path.getsize(filepath)} bytes)")

if __name__ == '__main__':
    create_sample_rock_image('assets/sample_images/rock_beat_sample.png')
    create_sample_fill_image('assets/sample_images/tom_fill_sample.png')
    print("All sample drum sheet images created successfully!")
