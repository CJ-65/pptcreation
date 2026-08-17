"""
Meridian Warmth — Architectural Interior Render
Corporate open-plan workstation bay, eye-level perspective
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import math
import os

W, H = 3840, 2160  # 4K

img = Image.new("RGB", (W, H), (255, 255, 255))
draw = ImageDraw.Draw(img)

# ─── Colour palette ────────────────────────────────────────────────────────────
SKY        = (220, 230, 242)
WALL_FAR   = (242, 239, 233)
WALL_MID   = (237, 233, 225)
WALL_NEAR  = (230, 225, 216)
TERRAZZO_L = (218, 215, 210)
TERRAZZO_D = (195, 192, 188)
WOOD_LIGHT = (185, 135,  80)
WOOD_MID   = (158, 108,  58)
WOOD_DARK  = (120,  78,  38)
WOOD_GRAIN = (140,  98,  52)
ORANGE     = (235, 110,  40)
CREAM      = (248, 245, 238)
BLACK_MESH = ( 28,  28,  30)
CHROME     = (195, 198, 202)
PALM_DARK  = ( 32,  68,  28)
PALM_MID   = ( 52,  98,  38)
PALM_LIGHT = ( 82, 138,  58)
PLANTER    = (110, 112, 115)
ART_MAT    = (250, 248, 244)
ART_FRAME  = ( 52,  48,  44)
BLIND_WOOD = (172, 132,  72)
BLIND_SHAD = (148, 112,  58)
SHADOW_A   = (  0,   0,   0, 35)
TEXT_COLOR = ( 88,  82,  74)

# ─── Perspective anchors ───────────────────────────────────────────────────────
# Vanishing point (VP) — slightly left of centre at eye level
VP_X = W * 0.42
VP_Y = H * 0.46   # eye level = 1.6 m

def lerp(a, b, t):
    return a + (b - a) * t

def vline(x0, y0, x1, y1, t):
    """Point on perspective line to VP at parameter t (0=near,1=far)"""
    return (lerp(x0, VP_X, t), lerp(y0, VP_Y, t),
            lerp(x1, VP_X, t), lerp(y1, VP_Y, t))

# ─── Sky / Ceiling ─────────────────────────────────────────────────────────────
# Gradient ceiling to sky through windows
for y in range(H):
    t = y / H
    if t < 0.08:   # ceiling strip
        r = int(lerp(232, 240, t/0.08))
        g = int(lerp(228, 236, t/0.08))
        b = int(lerp(220, 230, t/0.08))
    elif t < 0.46:  # wall / window zone
        nt = (t - 0.08) / 0.38
        r = int(lerp(240, 242, nt))
        g = int(lerp(236, 239, nt))
        b = int(lerp(230, 233, nt))
    else:           # floor zone
        nt = (t - 0.46) / 0.54
        r = int(lerp(230, 200, nt))
        g = int(lerp(226, 198, nt))
        b = int(lerp(220, 192, nt))
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# ─── Back wall ─────────────────────────────────────────────────────────────────
back_top    = int(H * 0.10)
back_bottom = int(H * 0.70)
back_left   = int(W * 0.05)
back_right  = int(W * 0.85)

draw.rectangle([back_left, back_top, back_right, back_bottom], fill=WALL_FAR)

# Subtle wall gradient (light source from left windows)
for x in range(back_left, back_right):
    t = (x - back_left) / (back_right - back_left)
    alpha = int(lerp(0, 28, t))
    draw.line([(x, back_top), (x, back_bottom)],
              fill=(max(0, WALL_FAR[0]-alpha), max(0, WALL_FAR[1]-alpha), max(0, WALL_FAR[2]-alpha)))

# ─── Floor ─────────────────────────────────────────────────────────────────────
floor_y = int(H * 0.70)
draw.rectangle([0, floor_y, W, H], fill=TERRAZZO_L)

# Terrazzo texture — small aggregate dots
rng = np.random.default_rng(42)
n_dots = 8000
xs = rng.integers(0, W, n_dots)
ys = rng.integers(floor_y, H, n_dots)
for xi, yi in zip(xs, ys):
    shade = rng.integers(170, 230)
    r_dot = rng.integers(1, 4)
    draw.ellipse([xi-r_dot, yi-r_dot, xi+r_dot, yi+r_dot],
                 fill=(shade, shade-3, shade-6))

# Floor reflection strip
for y in range(floor_y, floor_y + 120):
    alpha = int(lerp(40, 0, (y - floor_y) / 120))
    draw.line([(0, y), (W, y)],
              fill=(min(255, TERRAZZO_L[0]+alpha), min(255, TERRAZZO_L[1]+alpha), min(255, TERRAZZO_L[2]+alpha)))

# Terrazzo grid lines (3m bays)
grid_cols = 10
for i in range(grid_cols + 1):
    gx = int(i * W / grid_cols)
    draw.line([(gx, floor_y), (gx + int((H - floor_y)*0.3), H)],
              fill=(185, 182, 178), width=1)

# ─── Left window wall with venetian blinds ─────────────────────────────────────
win_left   = 0
win_right  = int(W * 0.18)
win_top    = int(H * 0.08)
win_bottom = int(H * 0.68)

# Exterior sky seen through window
for y in range(win_top, win_bottom):
    t = (y - win_top) / (win_bottom - win_top)
    r = int(lerp(210, 230, t))
    g = int(lerp(225, 235, t))
    b = int(lerp(245, 248, t))
    draw.line([(win_left, y), (win_right, y)], fill=(r, g, b))

# Venetian blind slats
slat_h = 18
gap    = 6
y_cursor = win_top + 30
slat_idx = 0
while y_cursor < win_bottom - slat_h:
    shade = BLIND_WOOD if slat_idx % 2 == 0 else BLIND_SHAD
    draw.rectangle([win_left, y_cursor, win_right, y_cursor + slat_h - 2], fill=shade)
    # Highlight edge of slat
    draw.line([(win_left, y_cursor), (win_right, y_cursor)],
              fill=(min(255,shade[0]+30), min(255,shade[1]+22), min(255,shade[2]+10)), width=2)
    y_cursor += slat_h + gap
    slat_idx += 1

# Blind shadow on floor and wall
for i in range(12):
    sx = win_right + i * 28
    shadow_w = 8
    draw.rectangle([sx, floor_y, sx + shadow_w, floor_y + 120],
                   fill=(TERRAZZO_D[0]-10, TERRAZZO_D[1]-10, TERRAZZO_D[2]-8))

# Window frame
draw.rectangle([win_left, win_top, win_right, win_bottom], outline=(200,196,190), width=4)
# Mullion
draw.line([(win_right//2, win_top), (win_right//2, win_bottom)], fill=(190,186,180), width=5)
draw.line([(win_left, int(lerp(win_top, win_bottom, 0.5))),
           (win_right, int(lerp(win_top, win_bottom, 0.5)))], fill=(190,186,180), width=4)

# Light column from window onto floor
window_beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
beam_draw = ImageDraw.Draw(window_beam)
beam_pts = [
    (win_right, win_top + 60),
    (win_right + 380, floor_y),
    (win_right - 30, floor_y),
    (win_left + 20, win_top + 60),
]
beam_draw.polygon(beam_pts, fill=(255, 252, 238, 18))
img = Image.alpha_composite(img.convert("RGBA"), window_beam).convert("RGB")
draw = ImageDraw.Draw(img)

# ─── Acoustic partition panels (orange + cream alternating) ────────────────────
# Panels are mid-height dividers between desk bays
panel_configs = [
    # (left_x, right_x, top_y, colour)
    (int(W*0.22), int(W*0.36), int(H*0.38), ORANGE),
    (int(W*0.36), int(W*0.50), int(H*0.40), CREAM),
    (int(W*0.50), int(W*0.64), int(H*0.42), ORANGE),
    (int(W*0.64), int(W*0.78), int(H*0.44), CREAM),
]
panel_bottom = int(H * 0.70)

for pl, pr, pt, col in panel_configs:
    # Panel body
    draw.rectangle([pl, pt, pr, panel_bottom], fill=col)
    # Fabric texture — subtle horizontal lines
    for fy in range(pt, panel_bottom, 6):
        shade_r = max(0, col[0] - 8)
        shade_g = max(0, col[1] - 6)
        shade_b = max(0, col[2] - 4)
        draw.line([(pl+2, fy), (pr-2, fy)], fill=(shade_r, shade_g, shade_b), width=1)
    # Highlight top edge
    draw.line([(pl, pt), (pr, pt)], fill=(min(255,col[0]+40), min(255,col[1]+35), min(255,col[2]+30)), width=3)
    # Side shadow
    draw.rectangle([pl, pt, pl+6, panel_bottom], fill=(max(0,col[0]-30), max(0,col[1]-25), max(0,col[2]-20)))
    # Panel border / aluminium trim
    draw.rectangle([pl, pt, pr, panel_bottom], outline=(160,155,150), width=2)

# ─── Cherry-wood desks ─────────────────────────────────────────────────────────
desk_configs = [
    # (left_x, right_x, desk_top_y, depth)
    (int(W*0.20), int(W*0.38), int(H*0.62), 55),
    (int(W*0.38), int(W*0.55), int(H*0.63), 55),
    (int(W*0.55), int(W*0.72), int(H*0.64), 55),
    (int(W*0.72), int(W*0.88), int(H*0.65), 55),
]

for dl, dr, dt, depth in desk_configs:
    db = dt + depth
    # Desk top surface (cherry veneer)
    for x in range(dl, dr):
        t = (x - dl) / max(1, dr - dl)
        r = int(lerp(WOOD_LIGHT[0], WOOD_DARK[0], t*0.4 + 0.1*math.sin(t*20)))
        g = int(lerp(WOOD_LIGHT[1], WOOD_DARK[1], t*0.4))
        b = int(lerp(WOOD_LIGHT[2], WOOD_DARK[2], t*0.4))
        draw.line([(x, dt), (x, db)], fill=(r, g, b))
    # Grain lines
    for gi in range(12):
        gx = dl + int((dr - dl) * gi / 12) + rng.integers(-8, 8)
        draw.line([(gx, dt), (gx + rng.integers(20,60), db)],
                  fill=(WOOD_GRAIN[0]-10, WOOD_GRAIN[1]-8, WOOD_GRAIN[2]-5), width=1)
    # Specular highlight on desk surface
    for y in range(dt, dt+12):
        t = (y - dt) / 12
        hl = int(lerp(60, 0, t))
        draw.line([(dl+40, y), (dr-40, y)],
                  fill=(min(255, WOOD_LIGHT[0]+hl), min(255, WOOD_LIGHT[1]+hl//2), min(255, WOOD_LIGHT[2])))
    # Desk front face (darker)
    desk_face_bottom = db + 48
    draw.rectangle([dl, db, dr, desk_face_bottom], fill=WOOD_DARK)
    # Desk legs
    leg_w = 14
    for lx in [dl + 20, dr - 20 - leg_w]:
        draw.rectangle([lx, desk_face_bottom, lx + leg_w, floor_y],
                       fill=(WOOD_DARK[0]-15, WOOD_DARK[1]-12, WOOD_DARK[2]-8))
    # Monitor (dark screen on desk)
    mon_cx = (dl + dr) // 2
    mon_w  = int((dr - dl) * 0.28)
    mon_h  = int(mon_w * 0.6)
    mon_y  = dt - mon_h - 12
    mon_x  = mon_cx - mon_w // 2
    draw.rectangle([mon_x, mon_y, mon_x + mon_w, dt - 12], fill=(22, 24, 28))
    draw.rectangle([mon_x+3, mon_y+3, mon_x+mon_w-3, dt-15], fill=(30, 48, 70))
    # Screen glow
    draw.rectangle([mon_x+4, mon_y+4, mon_x+mon_w//3, dt-16], fill=(40, 70, 120))
    # Monitor stand
    stand_x = mon_cx - 3
    draw.rectangle([stand_x, dt-12, stand_x+6, dt], fill=CHROME)
    draw.rectangle([stand_x-18, dt, stand_x+24, dt+6], fill=CHROME)

# ─── Black mesh ergonomic chairs ───────────────────────────────────────────────
chair_positions = [
    int(W*0.27), int(W*0.45), int(W*0.62), int(W*0.79)
]

for cx in chair_positions:
    seat_y  = int(H * 0.68)
    seat_w  = 95
    seat_h  = 28
    back_h  = 115
    back_w  = 85

    # Seat
    draw.ellipse([cx - seat_w//2, seat_y - seat_h//2,
                  cx + seat_w//2, seat_y + seat_h//2], fill=BLACK_MESH)
    # Backrest
    back_top  = seat_y - seat_h//2 - back_h
    back_left = cx - back_w//2
    back_right= cx + back_w//2
    draw.rounded_rectangle([back_left, back_top, back_right, seat_y - seat_h//2],
                            radius=12, fill=(38, 38, 42))
    # Mesh pattern on backrest
    for my in range(back_top+8, seat_y - seat_h//2 - 4, 10):
        draw.line([(back_left+6, my), (back_right-6, my)], fill=(55, 55, 62), width=2)
    for mx in range(back_left+8, back_right-6, 14):
        draw.line([(mx, back_top+6), (mx, seat_y-seat_h//2-4)], fill=(55, 55, 62), width=1)
    # Lumbar support line
    lumbar_y = back_top + int(back_h * 0.55)
    draw.line([(back_left+6, lumbar_y), (back_right-6, lumbar_y)], fill=CHROME, width=2)
    # Armrests
    arm_y = back_top + int(back_h * 0.6)
    for arm_dx in [-seat_w//2 - 8, seat_w//2 + 8 - 16]:
        draw.rectangle([cx + arm_dx, arm_y, cx + arm_dx + 16, arm_y + 28], fill=(45, 45, 50))
    # 5-star base
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        ex = int(cx + 52 * math.cos(rad))
        ey = int(floor_y - 8 + 22 * math.sin(rad) * 0.3)
        draw.line([(cx, floor_y - 8), (ex, ey)], fill=CHROME, width=6)
        draw.ellipse([ex-5, ey-4, ex+5, ey+4], fill=(150, 150, 155))
    # Central column
    draw.rectangle([cx-5, seat_y+seat_h//2, cx+5, floor_y-8], fill=CHROME)

# ─── Gallery wall — framed minimalist art prints ────────────────────────────────
gallery_wall_x = int(W * 0.87)
frame_configs = [
    # (cx, cy, fw, fh, art_type)
    (int(W*0.875), int(H*0.20), 180, 220, "lines"),
    (int(W*0.875), int(H*0.44), 180, 155, "circle"),
    (int(W*0.920), int(H*0.31), 130, 165, "grid"),
]

def draw_art_lines(d, fx, fy, fw, fh):
    """Sparse horizontal line study"""
    mat = 22
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    inner_l, inner_t = fx+mat+4, fy+mat+4
    inner_r, inner_b = fx+fw-mat-4, fy+fh-mat-4
    for li, t in enumerate([0.2, 0.35, 0.5, 0.62, 0.72, 0.80, 0.87]):
        y_art = int(lerp(inner_t, inner_b, t))
        line_len = int((inner_r - inner_l) * lerp(0.3, 0.9, li/7))
        start_x = inner_l + int((inner_r - inner_l - line_len) * 0.1)
        w_art = max(1, int(lerp(3, 1, t)))
        col_art = int(lerp(30, 140, t))
        d.line([(start_x, y_art), (start_x + line_len, y_art)],
               fill=(col_art, col_art-8, col_art-15), width=w_art)

def draw_art_circle(d, fx, fy, fw, fh):
    """Concentric circle study"""
    mat = 18
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    cx_art = fx + fw//2
    cy_art = fy + fh//2
    for r_art in [10, 25, 42, 58, 72, 82]:
        shade = int(lerp(20, 180, r_art/85))
        d.ellipse([cx_art-r_art, cy_art-r_art, cx_art+r_art, cy_art+r_art],
                  outline=(shade, shade-10, shade-20), width=2)

def draw_art_grid(d, fx, fy, fw, fh):
    """Minimalist grid composition"""
    mat = 16
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    inner_l = fx+mat+6; inner_t = fy+mat+6
    inner_r = fx+fw-mat-6; inner_b = fy+fh-mat-6
    cols_g = [0.0, 0.38, 0.62, 1.0]
    rows_g = [0.0, 0.30, 0.55, 0.75, 1.0]
    fills_g = [(20,20,22),(240,238,232),(20,20,22),(240,238,232),
               (240,238,232),(20,20,22),(240,238,232),(240,238,232),
               (20,20,22),(240,238,232),(20,20,22),(240,238,232)]
    fi = 0
    for ri in range(len(rows_g)-1):
        for ci in range(len(cols_g)-1):
            xl = inner_l + int((inner_r-inner_l)*cols_g[ci])
            xr = inner_l + int((inner_r-inner_l)*cols_g[ci+1])
            yt = inner_t + int((inner_b-inner_t)*rows_g[ri])
            yb = inner_t + int((inner_b-inner_t)*rows_g[ri+1])
            d.rectangle([xl+1, yt+1, xr-1, yb-1], fill=fills_g[fi % len(fills_g)])
            fi += 1

for (cx_f, cy_f, fw, fh, atype) in frame_configs:
    fx = cx_f - fw//2
    fy = cy_f - fh//2
    # Frame shadow
    draw.rectangle([fx+6, fy+6, fx+fw+6, fy+fh+6], fill=(180,175,168))
    # Frame
    draw.rectangle([fx, fy, fx+fw, fy+fh], fill=ART_FRAME)
    # Mat + art
    if atype == "lines":
        draw_art_lines(draw, fx, fy, fw, fh)
    elif atype == "circle":
        draw_art_circle(draw, fx, fy, fw, fh)
    elif atype == "grid":
        draw_art_grid(draw, fx, fy, fw, fh)
    # Frame border highlight
    draw.rectangle([fx, fy, fx+fw, fy+fh], outline=(75, 70, 62), width=4)

# ─── Potted palm plants ────────────────────────────────────────────────────────
def draw_palm(d, px, py, scale=1.0):
    """Draw a palm plant in a grey planter"""
    # Planter
    pw = int(88 * scale)
    ph = int(72 * scale)
    d.rectangle([px - pw//2, py - ph, px + pw//2, py], fill=PLANTER)
    d.rectangle([px - pw//2 + 4, py - ph + 4, px + pw//2 - 4, py - 4],
                fill=(125, 127, 130))
    d.rectangle([px - pw//2 - 6, py - int(ph*0.15), px + pw//2 + 6, py],
                fill=(100, 102, 105))
    # Trunk
    trunk_h = int(140 * scale)
    d.rectangle([px-5, py-ph-trunk_h, px+5, py-ph], fill=(72, 58, 38))
    # Fronds — radiate from top of trunk
    frond_base_y = py - ph - trunk_h
    fronds = [
        (-65, -95, 55, -40),
        (-110, -55, 25, -85),
        ( 65, -95, -55, -40),
        ( 110, -55, -25, -85),
        (-30, -120, 20, -30),
        ( 30, -120, -20, -30),
        (-80, -20, 10, -110),
        ( 80, -20, -10, -110),
    ]
    for (dx1, dy1, dx2, dy2) in fronds:
        x1 = int(px + dx1*scale); y1 = int(frond_base_y + dy1*scale)
        x2 = int(px + dx2*scale); y2 = int(frond_base_y + dy2*scale)
        # Main frond spine
        d.line([(px, frond_base_y), (x1, y1)], fill=PALM_MID, width=max(2, int(3*scale)))
        # Leaflets along the frond
        steps = 8
        for si in range(1, steps):
            t_leaf = si / steps
            lx = int(lerp(px, x1, t_leaf))
            ly = int(lerp(frond_base_y, y1, t_leaf))
            leaf_len = int(lerp(8, 28, math.sin(t_leaf * math.pi)) * scale)
            perp_x = int(-(y1 - frond_base_y) / max(1, abs(x1-px)+abs(y1-frond_base_y)) * leaf_len)
            perp_y = int( (x1 - px)           / max(1, abs(x1-px)+abs(y1-frond_base_y)) * leaf_len)
            col_leaf = PALM_LIGHT if si % 3 == 0 else PALM_MID
            d.line([(lx, ly), (lx+perp_x, ly+perp_y)], fill=col_leaf, width=max(1, int(2*scale)))
            d.line([(lx, ly), (lx-perp_x, ly-perp_y)], fill=col_leaf, width=max(1, int(2*scale)))

palm_positions = [
    (int(W*0.16), floor_y, 1.0),
    (int(W*0.84), floor_y, 0.85),
    (int(W*0.01), floor_y, 1.1),
]
for (px, py, sc) in palm_positions:
    draw_palm(draw, px, py, sc)

# ─── Ceiling (structural + light) ─────────────────────────────────────────────
ceiling_y = int(H * 0.08)
draw.rectangle([0, 0, W, ceiling_y], fill=(235, 232, 226))
# Exposed linear LED channels
for xi in range(6):
    led_x = int(W * (xi + 0.5) / 6)
    draw.rectangle([led_x - 2, 0, led_x + 2, ceiling_y], fill=(200,196,190))
    draw.rectangle([led_x - 1, 0, led_x + 1, ceiling_y], fill=(255, 255, 240))

# ─── Ambient occlusion / depth gradient (left edge darker) ─────────────────────
ao = Image.new("RGBA", (W, H), (0,0,0,0))
ao_draw = ImageDraw.Draw(ao)
for x in range(min(W, 280)):
    alpha = int(lerp(55, 0, x / 280))
    ao_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
# Right edge vignette
for x in range(max(0, W-200), W):
    alpha = int(lerp(0, 35, (x - (W-200)) / 200))
    ao_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
# Bottom vignette
for y in range(max(0, H-180), H):
    alpha = int(lerp(0, 50, (y - (H-180)) / 180))
    ao_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
img = Image.alpha_composite(img.convert("RGBA"), ao).convert("RGB")
draw = ImageDraw.Draw(img)

# ─── Subtle film grain ─────────────────────────────────────────────────────────
grain_arr = np.array(img, dtype=np.int16)
noise = rng.integers(-6, 7, size=(H, W, 3), dtype=np.int16)
grain_arr = np.clip(grain_arr + noise, 0, 255).astype(np.uint8)
img = Image.fromarray(grain_arr)
draw = ImageDraw.Draw(img)

# ─── Typography — Meridian Warmth label ───────────────────────────────────────
# Try system font, fall back gracefully
font_path = None
for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf",
           "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if os.path.exists(fp):
        font_path = fp
        break

try:
    font_label  = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
    font_sub    = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
except Exception:
    font_label = ImageFont.load_default()
    font_sub   = ImageFont.load_default()

label_text = "MERIDIAN WARMTH"
sub_text   = "Open-Plan Workstation Bay  ·  Architectural Visualization"

# Place at lower-left with generous margin
tx, ty = 58, H - 80
draw.text((tx+1, ty+1), label_text, font=font_label, fill=(0, 0, 0, 60))
draw.text((tx, ty),     label_text, font=font_label, fill=TEXT_COLOR)
draw.text((tx, ty + 38), sub_text,  font=font_sub,   fill=(130, 124, 115))

# ─── Subtle rule line above label ─────────────────────────────────────────────
draw.line([(tx, ty - 14), (tx + 420, ty - 14)], fill=(170, 164, 155), width=1)

# ─── Save ─────────────────────────────────────────────────────────────────────
out_path = "/home/user/pptcreation/meridian_warmth_render.png"
img = img.convert("RGB")

# Final sharpening pass
from PIL import ImageEnhance
enhancer = ImageEnhance.Sharpness(img)
img = enhancer.enhance(1.35)

img.save(out_path, "PNG", dpi=(300, 300), optimize=False)
print(f"Saved: {out_path}  ({img.size[0]}×{img.size[1]})")
