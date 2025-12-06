import sys
import math
import pygame
import numpy as np
from numba import njit, prange

# =======================
# App / Render Settings
# =======================
WIDTH, HEIGHT = 1000, 700
TARGET_FPS = 60

MAX_ITER_BASE = 600
MAX_ITER_BOOST_PER_DECADE = 60
ZOOM_STEP = 1.12
PAN_STEP = 0.06

# =======================
# Smooth Coloring Palette
# =======================
PALETTE_SIZE = 2048

def make_cosine_palette(n=PALETTE_SIZE):
    t = np.linspace(0, 1, n, endpoint=False, dtype=np.float32)
    r = (0.5 + 0.5*np.cos(2*np.pi*(t + 0.00)))**1.0
    g = (0.5 + 0.5*np.cos(2*np.pi*(t + 0.33)))**1.0
    b = (0.5 + 0.5*np.cos(2*np.pi*(t + 0.66)))**1.0
    palette = np.stack([r, g, b], axis=1)
    palette = (255.0 * palette).astype(np.uint8)
    return palette

PALETTE = make_cosine_palette()

# =======================
# Presets (including custom)
# =======================
PRESETS = [
    {"name":"Default Mandelbrot", "type":"mandelbrot", "center":(-0.5, 0.0), "zoom":1.0, "c":None},
    {"name":"Seahorse Valley", "type":"mandelbrot", "center":(-0.743643887037151, 0.13182590420533), "zoom":300.0, "c":None},
    {"name":"Elephant Valley", "type":"mandelbrot", "center":(0.285, 0.01), "zoom":350.0, "c":None},
    {"name":"Triple Spiral", "type":"mandelbrot", "center":(-0.1011, 0.633), "zoom":45.0, "c":None},
    {"name":"Spiral Galaxy", "type":"mandelbrot", "center":(-0.7613353729242306, 0.08357090531118005), "zoom":1100.0, "c":None},
    {"name":"Sun", "type":"mandelbrot", "center":(0.001643721971153, -0.822467633298876), "zoom":2.5e10, "c":None},
    {"name":"Double Spiral", "type":"mandelbrot", "center":(-0.0912, 0.651), "zoom":1700.0, "c":None},
    {"name":"Mini Mandelbrot", "type":"mandelbrot", "center":(-0.74543, 0.11301), "zoom":500000.0, "c":None},
    {"name":"Seahorse Tail", "type":"mandelbrot", "center":(-0.743566, 0.131402), "zoom":7000.0, "c":None},
    {"name":"Valley of the Dendrites", "type":"mandelbrot", "center":(-0.77568377, 0.13646737), "zoom":1800.0, "c":None},

    {"name":"Julia c=-0.8+0.156i (Classic)", "type":"julia", "center":(0.0, 0.0), "zoom":1.8, "c":(-0.8, 0.156)},
    {"name":"Julia c=-0.4+0.6i (Web)", "type":"julia", "center":(0.0, 0.0), "zoom":2.0, "c":(-0.4, 0.6)},
    {"name":"Julia c=0.285+0.01i (Elephant-ish)", "type":"julia", "center":(0.0, 0.0), "zoom":2.3, "c":(0.285, 0.01)},
    {"name":"Julia Island c=-0.70176-0.3842i", "type":"julia", "center":(0.0, 0.0), "zoom":2.1, "c":(-0.70176, -0.3842)},
    {"name":"Julia c=-0.835-0.2321i (Rabbit-ish)", "type":"julia", "center":(0.0, 0.0), "zoom":2.3, "c":(-0.835, -0.2321)},
    {"name":"Julia c=-0.7269+0.1889i (Dragon)", "type":"julia", "center":(0.0, 0.0), "zoom":2.2, "c":(-0.7269, 0.1889)},

    # Custom interactive mode (split-screen)
    {"name":"Custom Julia Explorer", "type":"custom", "center":(-0.5, 0.0), "zoom":1.0, "c":None},
]

# =======================
# Fractal Compute (Smooth Coloring)
# =======================
@njit(parallel=True, fastmath=True)
def render_fractal(width, height, x_center, y_center, zoom, max_iter, is_julia, c_re, c_im, palette):
    aspect = width / height
    span_x = 3.5 / zoom
    span_y = (3.5 / aspect) / zoom
    xmin = x_center - span_x * 0.5
    ymin = y_center - span_y * 0.5
    dx = span_x / width
    dy = span_y / height

    out = np.empty((width, height, 3), dtype=np.uint8)
    for i in prange(width):
        x0 = xmin + i * dx
        for j in range(height):
            y0 = ymin + j * dy

            if is_julia:
                zx = x0
                zy = y0
                cx = c_re
                cy = c_im
            else:
                zx = 0.0
                zy = 0.0
                cx = x0
                cy = y0

            it = 0
            while it < max_iter and (zx*zx + zy*zy) <= 4.0:
                xt = zx*zx - zy*zy + cx
                zy = 2.0*zx*zy + cy
                zx = xt
                it += 1

            if it < max_iter:
                mag2 = zx*zx + zy*zy
                if mag2 < 1.0:
                    mu = it
                else:
                    mu = it + 1.0 - math.log(math.log(mag2)) / math.log(2.0)
                idx = int(mu * 6.5) % PALETTE_SIZE
                out[i, j, 0] = palette[idx, 0]
                out[i, j, 1] = palette[idx, 1]
                out[i, j, 2] = palette[idx, 2]
            else:
                out[i, j, 0] = 0
                out[i, j, 1] = 0
                out[i, j, 2] = 0
    return out

# =======================
# Helpers
# =======================
def max_iter_for_zoom(zoom):
    boost = int(math.log10(max(zoom, 1.0)) * MAX_ITER_BOOST_PER_DECADE)
    return MAX_ITER_BASE + boost

def preset_to_state(p):
    if p["type"] == "mandelbrot" or p["type"] == "custom":
        return (p["center"][0], p["center"][1], p["zoom"], False, 0.0, 0.0)
    else:
        cx, cy = p["c"]
        return (0.0, 0.0, p["zoom"], True, cx, cy)

# =======================
# GUI Setup
# =======================
pygame.init()
flags = pygame.DOUBLEBUF
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("Fractal Explorer — Custom Julia Live")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 18)

PANEL_W = 280
ROW_H = 28
PADDING = 10

# initial state
preset_index = 0
x_center, y_center, zoom, is_julia, c_re, c_im = preset_to_state(PRESETS[preset_index])

dragging = False
last_mouse = (0, 0)

# caching (two-view support)
last_state_mandel = None
cached_mandel = None
last_state_julia = None
cached_julia = None

def draw_menu(surface, mouse_pos):
    panel_rect = pygame.Rect(0, 0, PANEL_W, HEIGHT)
    pygame.draw.rect(surface, (20, 22, 28), panel_rect)

    title = font.render("Presets (click to select)", True, (220, 220, 220))
    surface.blit(title, (PADDING, PADDING))

    y = PADDING*2 + 10
    for i, p in enumerate(PRESETS):
        r = pygame.Rect(PADDING, y, PANEL_W - 2*PADDING, ROW_H)
        hover = r.collidepoint(mouse_pos)
        color = (60, 65, 75) if i == preset_index else (40, 44, 52)
        if hover:
            color = (70, 76, 88)
        pygame.draw.rect(surface, color, r, border_radius=6)
        name_surf = font.render(p["name"], True, (240, 240, 240))
        surface.blit(name_surf, (r.x + 8, r.y + 5))
        y += ROW_H + 6

def compute_and_cache_mandel(view_w, view_h, x_c, y_c, z, iters, is_julia_local, cre, cim):
    global last_state_mandel, cached_mandel
    state = (x_c, y_c, z, is_julia_local, cre, cim, iters, view_w, view_h)
    if state == last_state_mandel and cached_mandel is not None:
        return
    img = render_fractal(view_w, view_h, x_c, y_c, z, iters, is_julia_local, cre, cim, PALETTE)
    cached_mandel = pygame.surfarray.make_surface(img)
    last_state_mandel = state

def compute_and_cache_julia(view_w, view_h, x_c, y_c, z, iters, cre, cim):
    global last_state_julia, cached_julia
    # julia is replaceable by state tuple
    state = (x_c, y_c, z, True, cre, cim, iters, view_w, view_h)
    if state == last_state_julia and cached_julia is not None:
        return
    img = render_fractal(view_w, view_h, x_c, y_c, z, iters, True, cre, cim, PALETTE)
    cached_julia = pygame.surfarray.make_surface(img)
    last_state_julia = state

def blit_mandel(x, y):
    if cached_mandel is not None:
        screen.blit(cached_mandel, (x, y))

def blit_julia(x, y):
    if cached_julia is not None:
        screen.blit(cached_julia, (x, y))

def zoom_at(mouse_x, mouse_y, factor, cur_x_center, cur_y_center, cur_zoom):
    # returns new (x_center, y_center, zoom) after zooming toward mouse_x, mouse_y
    if mouse_x < PANEL_W:
        return cur_x_center, cur_y_center, cur_zoom
    # convert mouse into fractal coords for the active view (may be half)
    view_w_full = WIDTH - PANEL_W
    px_full = (mouse_x - PANEL_W) / view_w_full
    py_full = mouse_y / HEIGHT
    # For single view uses full; for split custom mode we call this with proper coords
    aspect = view_w_full / HEIGHT
    span_x = 3.5 / cur_zoom
    span_y = (3.5 / aspect) / cur_zoom
    xmin = cur_x_center - span_x * 0.5
    ymin = cur_y_center - span_y * 0.5
    x_target = xmin + px_full * span_x
    y_target = ymin + py_full * span_y
    old_zoom = cur_zoom
    new_zoom = cur_zoom * factor
    lerp = 1.0 - (old_zoom / new_zoom)
    new_xc = cur_x_center + (x_target - cur_x_center) * lerp
    new_yc = cur_y_center + (y_target - cur_y_center) * lerp
    return new_xc, new_yc, new_zoom

# Warm-up JIT
_ = render_fractal(16, 16, -0.5, 0.0, 1.0, max_iter_for_zoom(1.0), False, 0.0, 0.0, PALETTE)

running = True
while running:
    dt = clock.tick(TARGET_FPS)
    mouse = pygame.mouse.get_pos()
    mx, my = mouse

    # Determine whether we're in custom mode
    current_preset = PRESETS[preset_index]
    in_custom_mode = (current_preset["type"] == "custom")

    # Prepare view sizes
    view_w_full = WIDTH - PANEL_W
    view_h = HEIGHT

    if in_custom_mode:
        # Split the view area into left (mandelbrot) and right (julia) halves
        left_w = view_w_full // 2
        right_w = view_w_full - left_w
        # Mandelbrot area uses current x_center,y_center,zoom
        # Julia on the right will use c from mouse position over left half
        # Live Julia uses reduced iterations
        mandel_iters = max_iter_for_zoom(zoom)
        julia_live_iters = max(80, int(mandel_iters * 0.28))
        # Compute Mandelbrot left view cache (render only left width)
        compute_and_cache_mandel(left_w, view_h, x_center, y_center, zoom, mandel_iters, False, 0.0, 0.0)

        # Determine c from mouse if mouse is over left-half; otherwise keep last known c_re,c_im
        live_c_re = c_re
        live_c_im = c_im
        if mx >= PANEL_W and mx < PANEL_W + left_w and my >= 0 and my < view_h:
            # Mouse inside left mandelbrot region
            px = (mx - PANEL_W) / left_w
            py = my / view_h
            aspect = left_w / view_h
            span_x = 3.5 / zoom
            span_y = (3.5 / aspect) / zoom
            xmin = x_center - span_x * 0.5
            ymin = y_center - span_y * 0.5
            live_c_re = xmin + px * span_x
            live_c_im = ymin + py * span_y
        # Render live julia on right using live_c_re/live_c_im
        # Julia's center and zoom: center (0,0), zoom 2.0 (good default) — but you can change to match mandelbrot zoom if you like
        julia_center_x, julia_center_y, julia_zoom = 0.0, 0.0, 2.0
        compute_and_cache_julia(right_w, view_h, julia_center_x, julia_center_y, julia_zoom, julia_live_iters, live_c_re, live_c_im)
    else:
        # Single view (no split) — compute the main cached_mandel as the full view (or the julia if is_julia)
        view_w = view_w_full
        main_iters = max_iter_for_zoom(zoom)
        if is_julia:
            compute_and_cache_julia(view_w, view_h, 0.0, 0.0, zoom, main_iters, c_re, c_im)
            # copy julia cache to the mandel cache variable so blit path is unified
            cached_mandel = cached_julia
            last_state_mandel = last_state_julia
        else:
            compute_and_cache_mandel(view_w, view_h, x_center, y_center, zoom, main_iters, False, 0.0, 0.0)
            # ensure julia cache not shown
            cached_julia = None
            last_state_julia = None

    # Draw background & fractals
    screen.fill((0, 0, 0))
    if in_custom_mode:
        # Draw left mandelbrot (at PANEL_W,0)
        blit_mandel(PANEL_W, 0)
        # Draw a thin separator line
        sep_x = PANEL_W + left_w
        pygame.draw.rect(screen, (12,12,12), (sep_x, 0, 2, view_h))
        # Draw right julia (at separator+2)
        blit_julia(sep_x + 2, 0)
    else:
        # single view
        blit_mandel(PANEL_W, 0)

    # Draw menu
    draw_menu(screen, mouse)

    # Coordinates display (for left fractal area; in custom mode use left half mapping)
    if in_custom_mode:
        left_w = view_w_full // 2
        if mx >= PANEL_W and mx < PANEL_W + left_w:
            px = (mx - PANEL_W) / left_w
            py = my / view_h
            aspect = left_w / view_h
            span_x = 3.5 / zoom
            span_y = (3.5 / aspect) / zoom
            xmin = x_center - span_x * 0.5
            ymin = y_center - span_y * 0.5
            coord_x = xmin + px * span_x
            coord_y = ymin + py * span_y
            coord_text = f"M: x={coord_x:.8f}, y={coord_y:.8f}"
            coord_text += f"  |  Live Julia c=({coord_x:.6f},{coord_y:.6f})"
            coords_surface = font.render(coord_text, True, (255,255,255))
            screen.blit(coords_surface, (PANEL_W + 10, HEIGHT - 25))
        else:
            # show general info
            coord_text = f"zoom={zoom:.3g}"
            coords_surface = font.render(coord_text, True, (255,255,255))
            screen.blit(coords_surface, (PANEL_W + 10, HEIGHT - 25))
    else:
        # single view coordinate mapping across full view
        if mx >= PANEL_W:
            px = (mx - PANEL_W) / (WIDTH - PANEL_W)
            py = my / view_h
            aspect = (WIDTH - PANEL_W) / view_h
            span_x = 3.5 / zoom
            span_y = (3.5 / aspect) / zoom
            xmin = x_center - span_x * 0.5
            ymin = y_center - span_y * 0.5
            coord_x = xmin + px * span_x
            coord_y = ymin + py * span_y
            coord_text = f"x={coord_x:.8f}, y={coord_y:.8f}"
            if is_julia:
                coord_text += f" | c=({c_re:.5f}, {c_im:.5f})"
            coords_surface = font.render(coord_text, True, (255,255,255))
            screen.blit(coords_surface, (PANEL_W + 10, HEIGHT - 25))

    # HUD
    mode_txt = "Julia" if is_julia else "Mandelbrot"
    info = f"{mode_txt} | preset: {PRESETS[preset_index]['name']} | zoom: {zoom:.3g} | fps: {int(clock.get_fps())}"
    hud = font.render(info, True, (255,255,255))
    screen.blit(hud, (PANEL_W + 10, 10))

    pygame.display.flip()

    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                last_mouse = event.pos
                # panel click?
                if event.pos[0] < PANEL_W:
                    y_top = PADDING*2 + 10
                    idx = (event.pos[1] - y_top) // (ROW_H + 6)
                    if 0 <= idx < len(PRESETS):
                        preset_index = int(idx)
                        x_center, y_center, zoom, is_julia, c_re, c_im = preset_to_state(PRESETS[preset_index])
                        # reset caches so next compute uses new preset
                        cached_mandel = None
                        last_state_mandel = None
                        cached_julia = None
                        last_state_julia = None

                else:
                    # If in custom mode and clicked left half, we may start drag selection for full-julia switch
                    pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
                # If in custom mode and mouse released inside left-half, switch to full Julia for that point
                if in_custom_mode:
                    left_w = view_w_full // 2
                    if event.pos[0] >= PANEL_W and event.pos[0] < PANEL_W + left_w:
                        # compute c from the release point
                        px = (event.pos[0] - PANEL_W) / left_w
                        py = event.pos[1] / view_h
                        aspect = left_w / view_h
                        span_x = 3.5 / zoom
                        span_y = (3.5 / aspect) / zoom
                        xmin = x_center - span_x * 0.5
                        ymin = y_center - span_y * 0.5
                        c_re = xmin + px * span_x
                        c_im = ymin + py * span_y
                        # Switch to full Julia view
                        is_julia = True
                        x_center, y_center = 0.0, 0.0
                        zoom = 2.0
                        cached_mandel = None
                        cached_julia = None
                        last_state_mandel = None
                        last_state_julia = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging and not in_custom_mode:
                # pan fractal (single view)
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                last_mouse = event.pos
                aspect = (WIDTH - PANEL_W) / HEIGHT
                span_x = 3.5 / zoom
                span_y = (3.5 / aspect) / zoom
                x_center -= dx / (WIDTH - PANEL_W) * span_x
                y_center -= dy / HEIGHT * span_y
                cached_mandel = None
            elif dragging and in_custom_mode:
                # dragging in custom mode pans the left mandelbrot half
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                last_mouse = event.pos
                # Only pan if dragging started within the left-half or the right-half is not clicked
                # We'll pan the Mandelbrot coordinates
                aspect = ( (WIDTH - PANEL_W) // 2 ) / HEIGHT
                span_x = 3.5 / zoom
                span_y = (3.5 / aspect) / zoom
                x_center -= dx / ((WIDTH - PANEL_W)//2) * span_x
                y_center -= dy / HEIGHT * span_y
                cached_mandel = None
                cached_julia = None

        elif event.type == pygame.MOUSEWHEEL:
            # interrupt nothing — immediate zooming
            if in_custom_mode:
                # determine whether wheel was over left-half or right-half (use mouse pos)
                if mx >= PANEL_W and mx < PANEL_W + (view_w_full // 2):
                    # zoom left mandelbrot (and keep julia live)
                    factor = ZOOM_STEP if event.y > 0 else (1.0 / ZOOM_STEP)
                    # zoom relative to left-half coordinates
                    left_w = view_w_full // 2
                    px = (mx - PANEL_W) / left_w
                    py = my / view_h
                    aspect = left_w / view_h
                    span_x = 3.5 / zoom
                    span_y = (3.5 / aspect) / zoom
                    xmin = x_center - span_x * 0.5
                    ymin = y_center - span_y * 0.5
                    x_target = xmin + px * span_x
                    y_target = ymin + py * span_y
                    old_zoom = zoom
                    zoom *= factor
                    lerp = 1.0 - (old_zoom / zoom)
                    x_center = x_center + (x_target - x_center) * lerp
                    y_center = y_center + (y_target - y_center) * lerp
                    cached_mandel = None
                    cached_julia = None
                else:
                    # wheel on right-half: zoom julia (only affects the right preview; when full julia view, it zooms normally)
                    # For live preview we keep julia zoom at fixed 2.0 to keep stable preview; but if user wants to zoom julia preview we can implement.
                    pass
            else:
                # single view zoom
                factor = ZOOM_STEP if event.y > 0 else (1.0 / ZOOM_STEP)
                x_center, y_center, zoom = zoom_at(mx, my, factor, x_center, y_center, zoom)
                cached_mandel = None
                cached_julia = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                # center zoom
                if in_custom_mode:
                    # zoom mandelbrot left view center
                    left_w = view_w_full // 2
                    mid_x = PANEL_W + left_w // 2
                    x_center, y_center, zoom = zoom_at(mid_x, HEIGHT//2, ZOOM_STEP, x_center, y_center, zoom)
                else:
                    x_center, y_center, zoom = zoom_at(PANEL_W + (WIDTH - PANEL_W)//2, HEIGHT//2, ZOOM_STEP, x_center, y_center, zoom)
                cached_mandel = None
                cached_julia = None
            elif event.key == pygame.K_MINUS:
                if in_custom_mode:
                    left_w = view_w_full // 2
                    mid_x = PANEL_W + left_w // 2
                    x_center, y_center, zoom = zoom_at(mid_x, HEIGHT//2, 1.0/ZOOM_STEP, x_center, y_center, zoom)
                else:
                    x_center, y_center, zoom = zoom_at(PANEL_W + (WIDTH - PANEL_W)//2, HEIGHT//2, 1.0/ZOOM_STEP, x_center, y_center, zoom)
                cached_mandel = None
                cached_julia = None
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                x_center -= PAN_STEP / zoom
                cached_mandel = None
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                x_center += PAN_STEP / zoom
                cached_mandel = None
            elif event.key in (pygame.K_UP, pygame.K_w):
                y_center -= PAN_STEP / zoom
                cached_mandel = None
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                y_center += PAN_STEP / zoom
                cached_mandel = None
            elif event.key == pygame.K_SPACE:
                # cycle preset (resets custom mode if appropriate)
                preset_index = (preset_index + 1) % len(PRESETS)
                x_center, y_center, zoom, is_julia, c_re, c_im = preset_to_state(PRESETS[preset_index])
                cached_mandel = None
                cached_julia = None
            elif event.key == pygame.K_j:
                # toggle julia (if current preset was mandelbrot or custom, derive c from center)
                is_julia = True
                if PRESETS[preset_index]["type"] == "julia":
                    c_re, c_im = PRESETS[preset_index]["c"]
                else:
                    # pick c as current center of mandelbrot (handy)
                    c_re, c_im = x_center, y_center
                x_center, y_center = 0.0, 0.0
                zoom = 2.0
                cached_mandel = None
                cached_julia = None
            elif event.key == pygame.K_m:
                # back to mandelbrot view (default preset)
                is_julia = False
                x_center, y_center, zoom, _, _, _ = preset_to_state(PRESETS[0])
                cached_mandel = None
                cached_julia = None

# Cleanup
pygame.quit()
sys.exit()
