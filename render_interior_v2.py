"""
Meridian Warmth — Architectural Interior Render v2
Refined pass: better perspective, atmospheric depth, material fidelity
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageChops
import numpy as np
import math
import os

W, H = 3840, 2160
img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

rng = np.random.default_rng(99)

# ─── Palette ───────────────────────────────────────────────────────────────────
def rgb(r,g,b): return (r,g,b)

CEIL_FAR    = rgb(238, 234, 228)
CEIL_NEAR   = rgb(228, 224, 216)
WALL_FAR    = rgb(245, 241, 235)
WALL_MID    = rgb(240, 236, 229)
TERRAZZO_1  = rgb(215, 212, 207)
TERRAZZO_2  = rgb(205, 202, 198)
GROUT       = rgb(185, 182, 178)
WOOD_AMB    = rgb(178, 126,  65)
WOOD_LIGHT  = rgb(195, 142,  78)
WOOD_MID    = rgb(162, 112,  55)
WOOD_DARK   = rgb(118,  74,  32)
WOOD_GRAIN  = rgb(138,  94,  46)
ORANGE_SAT  = rgb(228, 102,  32)
ORANGE_LIT  = rgb(242, 130,  55)
CREAM_SAT   = rgb(248, 244, 236)
CREAM_SHD   = rgb(232, 228, 220)
MESH_DARK   = rgb( 24,  24,  26)
MESH_MID    = rgb( 42,  42,  46)
CHROME      = rgb(192, 196, 200)
CHROME_HL   = rgb(218, 222, 226)
PALM_1      = rgb( 28,  62,  24)
PALM_2      = rgb( 48,  94,  36)
PALM_3      = rgb( 72, 130,  52)
PLANTER_D   = rgb(102, 104, 108)
PLANTER_L   = rgb(122, 124, 128)
ART_MAT     = rgb(251, 249, 245)
ART_FRAME   = rgb( 48,  44,  40)
SKY_TOP     = rgb(208, 222, 238)
SKY_BOT     = rgb(228, 236, 245)
BLIND_W     = rgb(168, 128,  68)
BLIND_S     = rgb(142, 108,  52)
TEXT_C      = rgb( 82,  76,  68)
TEXT_SUB    = rgb(140, 134, 124)

# ─── VP ────────────────────────────────────────────────────────────────────────
VP_X = W * 0.415
VP_Y = H * 0.455
EYE_Y = VP_Y   # 1.6m horizon

def lp(a, b, t): return a + (b - a) * t

def persp_y(real_y_m, cam_h=1.6, room_h=2.85, pix_top=0.08*H, pix_bot=0.70*H):
    """Convert real-world height (m from floor) to pixel Y"""
    frac = (cam_h - real_y_m) / cam_h if real_y_m <= cam_h else -(real_y_m - cam_h)/(room_h - cam_h)
    if real_y_m <= cam_h:
        return VP_Y + (pix_bot - VP_Y) * ((cam_h - real_y_m)/cam_h)
    else:
        return VP_Y - (VP_Y - pix_top) * ((real_y_m - cam_h)/(room_h - cam_h))

FLOOR_Y = int(persp_y(0))
CEIL_Y  = int(persp_y(2.85))

# ─── Sky gradient (background fill) ───────────────────────────────────────────
arr = np.zeros((H, W, 3), dtype=np.uint8)
for y in range(H):
    t = y / H
    if t < 0.46:  # above horizon / wall zone
        nt = t / 0.46
        arr[y, :] = [
            int(lp(WALL_FAR[0], WALL_MID[0], nt)),
            int(lp(WALL_FAR[1], WALL_MID[1], nt)),
            int(lp(WALL_FAR[2], WALL_MID[2], nt)),
        ]
    else:  # floor zone
        nt = (t - 0.46) / 0.54
        arr[y, :] = [
            int(lp(TERRAZZO_1[0], TERRAZZO_2[0], nt)),
            int(lp(TERRAZZO_1[1], TERRAZZO_2[1], nt)),
            int(lp(TERRAZZO_1[2], TERRAZZO_2[2], nt)),
        ]
img = Image.fromarray(arr)
draw = ImageDraw.Draw(img)

# ─── Ceiling ──────────────────────────────────────────────────────────────────
for y in range(0, CEIL_Y + 4):
    t = y / max(1, CEIL_Y)
    r = int(lp(CEIL_NEAR[0], CEIL_FAR[0], t))
    g = int(lp(CEIL_NEAR[1], CEIL_FAR[1], t))
    b = int(lp(CEIL_NEAR[2], CEIL_FAR[2], t))
    draw.line([(0, y), (W, y)], fill=(r,g,b))

# LED channels
for xi in range(7):
    lx = int(W * (xi + 0.3) / 7)
    draw.rectangle([lx-3, 0, lx+3, CEIL_Y+2], fill=(200,196,190))
    draw.rectangle([lx-1, 0, lx+1, CEIL_Y+2], fill=(255,254,245))
    # LED glow cone onto wall below
    cone = Image.new("RGBA", (W, H), (0,0,0,0))
    cd   = ImageDraw.Draw(cone)
    cone_pts = [(lx-60, CEIL_Y), (lx+60, CEIL_Y), (lx+180, CEIL_Y+340), (lx-180, CEIL_Y+340)]
    cd.polygon(cone_pts, fill=(255,252,230,12))
    img = Image.alpha_composite(img.convert("RGBA"), cone).convert("RGB")
    draw = ImageDraw.Draw(img)

# ─── Back wall with gradient ───────────────────────────────────────────────────
bw_l = int(W * 0.14); bw_r = int(W * 0.86)
bw_t = CEIL_Y; bw_b = FLOOR_Y
for x in range(bw_l, bw_r):
    t = (x - bw_l) / max(1, bw_r - bw_l)
    # Light from left windows, falls off right
    lit = int(lp(12, 0, t))
    r = min(255, WALL_FAR[0] + lit)
    g = min(255, WALL_FAR[1] + lit)
    b = min(255, WALL_FAR[2] + lit)
    draw.line([(x, bw_t), (x, bw_b)], fill=(r,g,b))

# ─── Floor ─────────────────────────────────────────────────────────────────────
for y in range(FLOOR_Y, H):
    nt = (y - FLOOR_Y) / max(1, H - FLOOR_Y)
    r = int(lp(TERRAZZO_1[0], TERRAZZO_2[0], nt))
    g = int(lp(TERRAZZO_1[1], TERRAZZO_2[1], nt))
    b = int(lp(TERRAZZO_1[2], TERRAZZO_2[2], nt))
    draw.line([(0, y), (W, y)], fill=(r,g,b))

# Terrazzo aggregate
n_dots = 14000
xs = rng.integers(0, W, n_dots)
ys = rng.integers(FLOOR_Y, H, n_dots)
for xi, yi in zip(xs, ys):
    sh = rng.integers(168, 220)
    rd = rng.integers(1, 5)
    draw.ellipse([xi-rd, yi-rd, xi+rd, yi+rd], fill=(sh, sh-2, sh-4))

# Floor grid — perspective-correct lines converging to VP
for xi in range(12):
    gx_near = int(W * xi / 11)
    draw.line([(gx_near, H), (int(VP_X), int(VP_Y))], fill=GROUT, width=1)
# Horizontal floor lines
for ri in range(12):
    fy = FLOOR_Y + int((H - FLOOR_Y) * (ri / 11) ** 0.7)
    # Scale line width with distance (closer = thicker)
    lw = max(1, int(lp(1, 2, ri/11)))
    draw.line([(0, fy), (W, fy)], fill=GROUT, width=lw)

# Gloss reflection on floor near window
refl = Image.new("RGBA", (W, H), (0,0,0,0))
rd   = ImageDraw.Draw(refl)
rd.rectangle([0, FLOOR_Y, int(W*0.22), FLOOR_Y+160],
             fill=(255, 252, 235, 22))
img = Image.alpha_composite(img.convert("RGBA"), refl).convert("RGB")
draw = ImageDraw.Draw(img)

# ─── Left window wall (venetian blinds) ───────────────────────────────────────
ww_l = 0; ww_r = int(W * 0.14)
ww_t = int(H * 0.06); ww_b = FLOOR_Y

# Sky outside
for y in range(ww_t, ww_b):
    t = (y - ww_t) / max(1, ww_b - ww_t)
    r = int(lp(SKY_TOP[0], SKY_BOT[0], t))
    g = int(lp(SKY_TOP[1], SKY_BOT[1], t))
    b = int(lp(SKY_TOP[2], SKY_BOT[2], t))
    draw.line([(ww_l, y), (ww_r, y)], fill=(r,g,b))

# Venetian slats
slat_h = 16; gap = 5; y_cur = ww_t + 28
si = 0
while y_cur < ww_b - slat_h - 2:
    shade = BLIND_W if si % 2 == 0 else BLIND_S
    draw.rectangle([ww_l, y_cur, ww_r, y_cur+slat_h-1], fill=shade)
    hl = (min(255,shade[0]+35), min(255,shade[1]+25), min(255,shade[2]+12))
    shd= (max(0,shade[0]-20), max(0,shade[1]-15), max(0,shade[2]-8))
    draw.line([(ww_l, y_cur), (ww_r, y_cur)], fill=hl, width=2)
    draw.line([(ww_l, y_cur+slat_h-1), (ww_r, y_cur+slat_h-1)], fill=shd, width=1)
    y_cur += slat_h + gap; si += 1

# Window frame + mullion
draw.rectangle([ww_l, ww_t, ww_r, ww_b], outline=(195,190,183), width=5)
mid_x = ww_r // 2
mid_y = (ww_t + ww_b) // 2
draw.line([(mid_x, ww_t), (mid_x, ww_b)], fill=(185,180,173), width=6)
draw.line([(ww_l, mid_y), (ww_r, mid_y)], fill=(185,180,173), width=5)

# Daylight beam — polygon fanning from window into room
beam = Image.new("RGBA", (W, H), (0,0,0,0))
bd   = ImageDraw.Draw(beam)
bd.polygon([(ww_r, ww_t+80), (ww_r+520, FLOOR_Y), (ww_r-10, FLOOR_Y), (ww_l+15, ww_t+80)],
           fill=(255,250,230,16))
img = Image.alpha_composite(img.convert("RGBA"), beam).convert("RGB")
draw = ImageDraw.Draw(img)

# Blind shadow bars on back wall and floor
for bi in range(18):
    sx = ww_r + bi * 26
    if sx > W: break
    shadow_top = CEIL_Y + bi*18
    draw.rectangle([sx, shadow_top, sx+9, FLOOR_Y], fill=(210,206,200))
    draw.rectangle([sx, FLOOR_Y, sx+9, FLOOR_Y+120], fill=(TERRAZZO_2[0]-12, TERRAZZO_2[1]-12, TERRAZZO_2[2]-10))

# ─── Acoustic partition panels ─────────────────────────────────────────────────
panel_defs = [
    (int(W*0.21), int(W*0.34), int(H*0.37), ORANGE_SAT, ORANGE_LIT),
    (int(W*0.34), int(W*0.47), int(H*0.39), CREAM_SAT,  CREAM_SHD),
    (int(W*0.47), int(W*0.60), int(H*0.41), ORANGE_SAT, ORANGE_LIT),
    (int(W*0.60), int(W*0.73), int(H*0.43), CREAM_SAT,  CREAM_SHD),
]
PB = FLOOR_Y - 10  # panel bottom

for pl, pr, pt, col_base, col_lit in panel_defs:
    # Ambient occlusion under panel
    draw.rectangle([pl+6, PB-4, pr-6, PB+8], fill=(180,176,170))
    # Panel body with left-light gradient
    for x in range(pl, pr):
        t = (x - pl) / max(1, pr - pl)
        # Left side lit, right side in shadow
        lit = int(lp(20, -15, t))
        r = min(255, max(0, col_base[0] + lit))
        g = min(255, max(0, col_base[1] + lit))
        b = min(255, max(0, col_base[2] + lit))
        draw.line([(x, pt), (x, PB)], fill=(r,g,b))
    # Fabric weave texture
    for fy2 in range(pt+2, PB-2, 5):
        shd = (max(0,col_base[0]-10), max(0,col_base[1]-8), max(0,col_base[2]-5))
        draw.line([(pl+4, fy2), (pr-4, fy2)], fill=shd, width=1)
    for fx2 in range(pl+4, pr-4, 8):
        shd = (max(0,col_base[0]-6), max(0,col_base[1]-5), max(0,col_base[2]-3))
        draw.line([(fx2, pt+2), (fx2, PB-2)], fill=shd, width=1)
    # Top highlight
    draw.line([(pl+2, pt), (pr-2, pt)],
              fill=(min(255,col_lit[0]+30), min(255,col_lit[1]+25), min(255,col_lit[2]+18)), width=3)
    # Left shadow edge
    draw.rectangle([pl, pt, pl+8, PB], fill=(max(0,col_base[0]-35), max(0,col_base[1]-28), max(0,col_base[2]-20)))
    # Aluminium trim
    draw.rectangle([pl, pt, pr, PB], outline=(152,148,142), width=2)
    # Bottom rubber foot strip
    draw.rectangle([pl+10, PB-4, pr-10, PB+2], fill=(100,96,90))

# ─── Cherry-wood desks ─────────────────────────────────────────────────────────
desk_defs = [
    (int(W*0.19), int(W*0.35), int(H*0.615), 52),
    (int(W*0.35), int(W*0.50), int(H*0.625), 52),
    (int(W*0.50), int(W*0.65), int(H*0.635), 52),
    (int(W*0.65), int(W*0.80), int(H*0.645), 52),
]

for dl, dr, dt, dep in desk_defs:
    db = dt + dep
    # Desk top: cherry veneer with cross-grain
    for x in range(dl, dr):
        t = (x - dl) / max(1, dr - dl)
        # Base wood tone with subtle variation
        base_r = int(lp(WOOD_LIGHT[0], WOOD_AMB[0], t))
        base_g = int(lp(WOOD_LIGHT[1], WOOD_AMB[1], t))
        base_b = int(lp(WOOD_LIGHT[2], WOOD_AMB[2], t))
        # Grain modulation
        grain = int(8 * math.sin(t * 60 + 0.3) + 5 * math.sin(t * 22))
        draw.line([(x, dt), (x, db)],
                  fill=(min(255,max(0,base_r+grain)), min(255,max(0,base_g+grain//2)), min(255,max(0,base_b))))
    # Specular streak (window light)
    hl_cx = dl + int((dr-dl)*0.35)
    for y in range(dt, dt+10):
        t = (y - dt) / 10
        hl = int(lp(55, 0, t**0.5))
        draw.line([(hl_cx-80, y), (hl_cx+120, y)],
                  fill=(min(255,WOOD_LIGHT[0]+hl), min(255,WOOD_LIGHT[1]+hl//3), min(255,WOOD_LIGHT[2])))
    # Front face (darker)
    face_b = db + 52
    for y in range(db, face_b):
        t = (y - db) / max(1, face_b - db)
        r = int(lp(WOOD_MID[0], WOOD_DARK[0], t))
        g = int(lp(WOOD_MID[1], WOOD_DARK[1], t))
        b_c = int(lp(WOOD_MID[2], WOOD_DARK[2], t))
        draw.line([(dl, y), (dr, y)], fill=(r,g,b_c))
    # Edge highlight (top edge chamfer)
    draw.line([(dl, dt), (dr, dt)], fill=(min(255,WOOD_LIGHT[0]+45), min(255,WOOD_LIGHT[1]+30), min(255,WOOD_LIGHT[2]+10)), width=2)
    # Desk shadow on floor
    shadow_layer = Image.new("RGBA", (W, H), (0,0,0,0))
    sld = ImageDraw.Draw(shadow_layer)
    sld.polygon([(dl+20, face_b), (dr-20, face_b), (dr+20, FLOOR_Y), (dl-20, FLOOR_Y)],
                fill=(0,0,0,28))
    img = Image.alpha_composite(img.convert("RGBA"), shadow_layer).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Legs
    for lx in [dl+22, dr-36]:
        draw.rectangle([lx, face_b, lx+14, FLOOR_Y], fill=(WOOD_DARK[0]-12, WOOD_DARK[1]-10, WOOD_DARK[2]-6))
        # Leg highlight
        draw.line([(lx+1, face_b), (lx+1, FLOOR_Y)], fill=(WOOD_MID[0], WOOD_MID[1], WOOD_MID[2]), width=2)
    # Monitor
    mon_cx = (dl + dr) // 2
    mon_w  = int((dr - dl) * 0.30)
    mon_h  = int(mon_w * 0.62)
    mon_x  = mon_cx - mon_w//2
    mon_y  = dt - mon_h - 14
    # Monitor housing
    draw.rounded_rectangle([mon_x-4, mon_y-4, mon_x+mon_w+4, dt-10], radius=6, fill=(35,36,40))
    # Screen
    draw.rectangle([mon_x, mon_y, mon_x+mon_w, dt-14], fill=(18,22,30))
    # Screen content glow
    draw.rectangle([mon_x+4, mon_y+4, mon_x+mon_w//2, dt-18], fill=(28,52,98))
    draw.rectangle([mon_x+mon_w//2+2, mon_y+4, mon_x+mon_w-4, mon_y+mon_h//3], fill=(38,68,62))
    # Monitor base
    draw.rectangle([mon_cx-5, dt-14, mon_cx+5, dt], fill=CHROME)
    draw.rectangle([mon_cx-22, dt, mon_cx+22, dt+7], fill=CHROME)
    draw.line([(mon_cx-22, dt), (mon_cx+22, dt)], fill=CHROME_HL, width=2)

# ─── Ergonomic chairs ──────────────────────────────────────────────────────────
chair_xs = [int(W*0.26), int(W*0.43), int(W*0.58), int(W*0.74)]

for cx in chair_xs:
    seat_y = FLOOR_Y - 5
    seat_w = 105; seat_h = 32
    back_h = 128; back_w = 90

    # Chair shadow on floor
    sl = Image.new("RGBA", (W,H),(0,0,0,0))
    sld2 = ImageDraw.Draw(sl)
    sld2.ellipse([cx-48, FLOOR_Y-8, cx+48, FLOOR_Y+18], fill=(0,0,0,35))
    img = Image.alpha_composite(img.convert("RGBA"), sl).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Seat cushion
    draw.ellipse([cx-seat_w//2, seat_y-seat_h//2, cx+seat_w//2, seat_y+seat_h//2], fill=MESH_DARK)
    draw.ellipse([cx-seat_w//2+3, seat_y-seat_h//2+3, cx+seat_w//2-3, seat_y+seat_h//2-3],
                 fill=(32,32,36))

    # Backrest
    bt = seat_y - seat_h//2 - back_h
    bl = cx - back_w//2; br = cx + back_w//2
    draw.rounded_rectangle([bl, bt, br, seat_y-seat_h//2], radius=14, fill=MESH_DARK)
    draw.rounded_rectangle([bl+2, bt+2, br-2, seat_y-seat_h//2-2], radius=12, fill=MESH_MID)
    # Mesh grid
    for my in range(bt+8, seat_y-seat_h//2-4, 9):
        draw.line([(bl+7, my), (br-7, my)], fill=(52,52,58), width=2)
    for mx2 in range(bl+8, br-7, 13):
        draw.line([(mx2, bt+8), (mx2, seat_y-seat_h//2-4)], fill=(52,52,58), width=1)
    # Backrest highlight
    draw.line([(bl+3, bt+3), (br-3, bt+3)], fill=(60,60,66), width=2)
    # Lumbar support bar
    lumbar = bt + int(back_h*0.52)
    draw.rectangle([bl+6, lumbar-2, br-6, lumbar+3], fill=CHROME)
    draw.line([(bl+6, lumbar-2), (br-6, lumbar-2)], fill=CHROME_HL, width=1)

    # Armrests
    arm_y = bt + int(back_h * 0.58)
    for adx in [-seat_w//2-10, seat_w//2-6]:
        draw.rounded_rectangle([cx+adx, arm_y, cx+adx+16, arm_y+30], radius=4, fill=MESH_MID)
        draw.rectangle([cx+adx+2, arm_y+2, cx+adx+14, arm_y+10], fill=(52,52,58))

    # Pneumatic column
    col_top = min(seat_y+seat_h//2, FLOOR_Y)
    col_bot = max(seat_y+seat_h//2, FLOOR_Y+2)
    draw.rectangle([cx-6, col_top, cx+6, col_bot], fill=CHROME)
    draw.line([(cx-1, col_top), (cx-1, col_bot)], fill=CHROME_HL, width=2)

    # 5-star base
    for ai in range(5):
        ang = math.radians(ai * 72 - 18)
        ex = int(cx + 54 * math.cos(ang))
        ey = int(FLOOR_Y + 5 + int(18 * math.sin(ang) * 0.25))
        draw.line([(cx, FLOOR_Y+2), (ex, ey)], fill=CHROME, width=7)
        draw.ellipse([ex-7, ey-5, ex+7, ey+5], fill=CHROME)
        draw.ellipse([ex-4, ey-3, ex+4, ey+3], fill=CHROME_HL)

# ─── Gallery wall ──────────────────────────────────────────────────────────────
frames = [
    (int(W*0.873), int(H*0.185), 192, 238, "lines_v"),
    (int(W*0.873), int(H*0.455), 192, 162, "circle_v"),
    (int(W*0.917), int(H*0.315), 140, 178, "grid_v"),
]

def lines_v(d, fx, fy, fw, fh):
    mat = 24
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    il = fx+mat+6; it = fy+mat+6; ir = fx+fw-mat-6; ib = fy+fh-mat-6
    for li, t in enumerate([0.12, 0.28, 0.42, 0.54, 0.65, 0.74, 0.82, 0.89]):
        yy = int(lp(it, ib, t))
        llen = int((ir - il) * lp(0.22, 0.88, li/8))
        sx = il + int((ir-il-llen)*0.08)
        ww2 = max(1, 4 - li//2)
        cv = int(lp(22, 155, t))
        d.line([(sx, yy), (sx+llen, yy)], fill=(cv, cv-6, cv-12), width=ww2)

def circle_v(d, fx, fy, fw, fh):
    mat = 20
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    cxc = fx+fw//2; cyc = fy+fh//2
    for rv in [8, 20, 34, 48, 60, 70, 78]:
        sv = int(lp(18, 185, rv/80))
        d.ellipse([cxc-rv, cyc-rv, cxc+rv, cyc+rv], outline=(sv, sv-8, sv-16), width=2)
    # Single cross-hair
    d.line([(cxc-82, cyc), (cxc+82, cyc)], fill=(190,185,178), width=1)
    d.line([(cxc, cyc-65), (cxc, cyc+65)], fill=(190,185,178), width=1)

def grid_v(d, fx, fy, fw, fh):
    mat = 18
    d.rectangle([fx+mat, fy+mat, fx+fw-mat, fy+fh-mat], fill=ART_MAT)
    il = fx+mat+5; it = fy+mat+5; ir = fx+fw-mat-5; ib = fy+fh-mat-5
    cs = [0.0, 0.40, 0.65, 1.0]
    rs = [0.0, 0.28, 0.52, 0.73, 1.0]
    fills2 = [(20,20,22),(ART_MAT[0],ART_MAT[1],ART_MAT[2]),(20,20,22),(ART_MAT[0],ART_MAT[1],ART_MAT[2]),
              (ART_MAT[0],ART_MAT[1],ART_MAT[2]),(20,20,22),(ART_MAT[0],ART_MAT[1],ART_MAT[2]),(ART_MAT[0],ART_MAT[1],ART_MAT[2]),
              (20,20,22),(ART_MAT[0],ART_MAT[1],ART_MAT[2]),(20,20,22),(ART_MAT[0],ART_MAT[1],ART_MAT[2])]
    fi = 0
    for ri in range(len(rs)-1):
        for ci in range(len(cs)-1):
            xl = il+int((ir-il)*cs[ci]); xr = il+int((ir-il)*cs[ci+1])
            yt = it+int((ib-it)*rs[ri]); yb = it+int((ib-it)*rs[ri+1])
            d.rectangle([xl+1,yt+1,xr-1,yb-1], fill=fills2[fi % 12]); fi+=1

art_fns = {"lines_v": lines_v, "circle_v": circle_v, "grid_v": grid_v}

for (cxf, cyf, fw, fh, atype) in frames:
    fx = cxf - fw//2; fy = cyf - fh//2
    # Drop shadow
    draw.rectangle([fx+7, fy+7, fx+fw+7, fy+fh+7], fill=(165,160,154))
    # Frame body
    draw.rectangle([fx, fy, fx+fw, fy+fh], fill=ART_FRAME)
    # Art
    art_fns[atype](draw, fx, fy, fw, fh)
    # Frame bevel
    draw.rectangle([fx, fy, fx+fw, fy+fh], outline=(68,64,58), width=5)
    draw.rectangle([fx+2, fy+2, fx+fw-2, fy+fh-2], outline=(38,34,30), width=2)

# ─── Palm plants ───────────────────────────────────────────────────────────────
def draw_palm_v2(d, px, py_floor, sc=1.0):
    pw = int(90*sc); ph = int(78*sc)
    # Planter
    for yi in range(py_floor-ph, py_floor):
        t = (yi-(py_floor-ph))/max(1,ph)
        r = int(lp(PLANTER_L[0], PLANTER_D[0], t))
        g = int(lp(PLANTER_L[1], PLANTER_D[1], t))
        b = int(lp(PLANTER_L[2], PLANTER_D[2], t))
        d.line([(px-int(pw*(0.5+t*0.08)), yi), (px+int(pw*(0.5+t*0.08)), yi)], fill=(r,g,b))
    # Planter rim
    d.rectangle([px-pw//2-8, py_floor-ph-5, px+pw//2+8, py_floor-ph+8], fill=PLANTER_L)
    d.rectangle([px-pw//2-7, py_floor-ph-4, px+pw//2+7, py_floor-ph+7], fill=(135,137,140))

    trunk_h = int(155*sc)
    # Trunk
    for yi in range(py_floor-ph-trunk_h, py_floor-ph):
        t = (yi-(py_floor-ph-trunk_h))/max(1,trunk_h)
        tw = max(3, int(lp(4,8,1-t)*sc))
        d.line([(px-tw, yi), (px+tw, yi)], fill=(int(lp(78,62,t)), int(lp(62,48,t)), int(lp(40,30,t))))

    base_y = py_floor - ph - trunk_h
    frond_data = [
        (-70,-105,60,-42,0.9),(-115,-60,28,-92,0.75),(68,-105,-58,-42,0.9),(112,-60,-28,-92,0.75),
        (-32,-128,22,-32,1.0),(32,-128,-22,-32,1.0),(-85,-22,12,-118,0.70),(85,-22,-12,-118,0.70),
        (-50,-70,55,-115,0.6),(50,-70,-55,-115,0.6),
    ]
    for (dx1,dy1,dx2,dy2,fr_sc) in frond_data:
        x1=int(px+dx1*sc); y1=int(base_y+dy1*sc)
        steps=10
        pts=[(px,base_y)]
        for si in range(1,steps+1):
            t=si/steps
            cx_f=px + int(lp(0,dx1*sc,t) + lp(0,dx2*sc,t)*0.25*math.sin(t*math.pi))
            cy_f=base_y+int(lp(0,dy1*sc,t)+lp(0,dy2*sc,t)*0.25*math.sin(t*math.pi))
            pts.append((cx_f,cy_f))
        # Draw frond spine
        for pi2 in range(len(pts)-1):
            col_f = PALM_2 if pi2 < steps//2 else PALM_3
            d.line([pts[pi2], pts[pi2+1]], fill=col_f, width=max(1,int(3*sc*fr_sc*(1-pi2/steps*0.7))))
            # Leaflets
            if pi2 > 1:
                seg_x=pts[pi2][0]-pts[pi2-1][0]; seg_y=pts[pi2][1]-pts[pi2-1][1]
                seg_len=max(1,math.sqrt(seg_x**2+seg_y**2))
                perp_x=-seg_y/seg_len; perp_y=seg_x/seg_len
                ll=int(lp(5,28,math.sin(pi2/steps*math.pi))*sc)
                lx_b=pts[pi2][0]; ly_b=pts[pi2][1]
                lc = PALM_3 if pi2%3!=0 else PALM_2
                d.line([(lx_b,ly_b),(int(lx_b+perp_x*ll),int(ly_b+perp_y*ll))], fill=lc, width=max(1,int(sc)))
                d.line([(lx_b,ly_b),(int(lx_b-perp_x*ll),int(ly_b-perp_y*ll))], fill=lc, width=max(1,int(sc)))

draw_palm_v2(draw, int(W*0.155), FLOOR_Y, 1.02)
draw_palm_v2(draw, int(W*0.845), FLOOR_Y, 0.88)
draw_palm_v2(draw, int(W*0.015), FLOOR_Y, 1.12)

# ─── Global light/shadow compositing ──────────────────────────────────────────
# Atmospheric depth: far objects slightly lighter (aerial perspective)
depth_layer = Image.new("RGBA", (W, H), (0,0,0,0))
dd = ImageDraw.Draw(depth_layer)
# Left-right vignette
for x in range(min(W,300)):
    a = int(lp(60, 0, x/300)**1.2)
    dd.line([(x,0),(x,H)], fill=(0,0,0,a))
for x in range(max(0,W-250), W):
    a = int(lp(0, 40, (x-(W-250))/250))
    dd.line([(x,0),(x,H)], fill=(0,0,0,a))
# Bottom vignette
for y in range(max(0,H-220), H):
    a = int(lp(0, 55, (y-(H-220))/220))
    dd.line([(0,y),(W,y)], fill=(0,0,0,a))
# Top vignette (subtle ceiling darkening)
for y in range(min(H,80)):
    a = int(lp(30, 0, y/80))
    dd.line([(0,y),(W,y)], fill=(0,0,0,a))
img = Image.alpha_composite(img.convert("RGBA"), depth_layer).convert("RGB")

# ─── Film grain + final sharpening ────────────────────────────────────────────
arr2 = np.array(img, dtype=np.int16)
noise2 = rng.integers(-5, 6, size=(H, W, 3), dtype=np.int16)
arr2 = np.clip(arr2 + noise2, 0, 255).astype(np.uint8)
img = Image.fromarray(arr2)

# Selective unsharp mask
from PIL import ImageFilter
sharp = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=2))
img = Image.blend(img, sharp, 0.65)

# Warm tone lift (slightly golden)
arr3 = np.array(img, dtype=np.float32)
arr3[:,:,0] = np.clip(arr3[:,:,0] * 1.018, 0, 255)  # warm red
arr3[:,:,2] = np.clip(arr3[:,:,2] * 0.988, 0, 255)  # cool blue down
img = Image.fromarray(arr3.astype(np.uint8))
draw = ImageDraw.Draw(img)

# ─── Typography ────────────────────────────────────────────────────────────────
font_path = None
font_paths = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]
for fp in font_paths:
    if os.path.exists(fp):
        font_path = fp; break

try:
    f_label = ImageFont.truetype(font_path, 30) if font_path else ImageFont.load_default()
    f_sub   = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    f_tiny  = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
except Exception:
    f_label = ImageFont.load_default(); f_sub = f_label; f_tiny = f_label

tx, ty = 64, H - 90
# Rule line
draw.line([(tx, ty-16), (tx+460, ty-16)], fill=(162,156,146), width=1)
# Label + shadow
draw.text((tx+1, ty+1), "MERIDIAN WARMTH", font=f_label, fill=(0,0,0,50))
draw.text((tx, ty),     "MERIDIAN WARMTH", font=f_label, fill=TEXT_C)
draw.text((tx, ty+38),  "Open-Plan Workstation Bay  ·  Architectural Study", font=f_sub, fill=TEXT_SUB)
# Small datum mark — lower right
draw.text((W-220, H-38), "8K  ·  V-RAY STUDY", font=f_tiny, fill=(165,158,148))

# ─── Save ──────────────────────────────────────────────────────────────────────
out = "/home/user/pptcreation/meridian_warmth_final.png"
img.save(out, "PNG", dpi=(300, 300))
print(f"Saved: {out}  ({img.size[0]}×{img.size[1]})")
