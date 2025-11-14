"""
Galaxy Nebula Screensaver (Enhanced Aesthetic + Black Background)
- Rainbow meteor showers
- Spark bursts when meteors fade out
- Smooth glowing starfield
- Subtle nebula gradient
- Opaque black cosmic background
- No mouse-click pause
- Global hotkey toggle (Ctrl + Shift + `)
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pygame, math, random, time, threading, keyboard
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# === CONFIG ===
STAR_COUNT = 950
METEOR_COUNT = 25
SPARK_COUNT = 80
TOGGLE_HOTKEY = "ctrl+shift+`"
ROTATION_SPEED = 0.1
FADE_SPEED = 0.012

screensaver_on = False
running_screensaver = False


# === STARFIELD ===
def generate_stars():
    stars = []
    for _ in range(STAR_COUNT):
        x = random.uniform(-50, 50)
        y = random.uniform(-30, 30)
        z = random.uniform(-100, -5)
        speed = random.uniform(0.05, 0.2)
        hue = random.choice([
            (0.65, 0.8, 1.0),
            (0.5, 0.7, 1.0),
            (0.8, 0.85, 1.0),
            (0.4, 0.9, 1.0),
            (0.7, 0.9, 1.0)
        ])
        stars.append([x, y, z, speed, hue])
    return stars


def draw_stars(stars, phase):
    glPointSize(2.5)
    glBegin(GL_POINTS)
    for s in stars:
        x, y, z, speed, hue = s
        twinkle = (math.sin(phase * 2 + x + y) + 1.3) / 2.3
        glow = 0.3 + 0.7 * twinkle
        glColor4f(hue[0] * glow, hue[1] * glow, hue[2] * glow, 1.0)
        glVertex3f(x, y, z)

        # smooth swirl motion
        angle = math.atan2(y, x) + 0.0008 * speed
        radius = math.hypot(x, y)
        radius *= 0.9998
        s[0] = radius * math.cos(angle)
        s[1] = radius * math.sin(angle)
        s[2] += speed * 0.4

        if s[2] > -1:
            s[0] = random.uniform(-50, 50)
            s[1] = random.uniform(-30, 30)
            s[2] = random.uniform(-100, -5)
    glEnd()


# === METEORS ===
def generate_meteors():
    meteors = []
    for _ in range(METEOR_COUNT):
        reset_meteor(meteors)
    return meteors


def reset_meteor(meteors, existing=None):
    if existing:
        m = existing
    else:
        m = [0, 0, 0, 0, 0, 0]
    m[0] = random.uniform(70, 95)
    m[1] = random.uniform(35, 55)
    m[2] = random.uniform(-60, -25)
    m[3] = random.uniform(0.6, 1.3)
    m[4] = random.uniform(0, 2 * math.pi)
    m[5] = 0
    if existing is None:
        meteors.append(m)
    return m


def draw_meteors(meteors, phase, sparks):
    glBegin(GL_LINES)
    for m in meteors:
        x, y, z, speed, color_phase, _ = m
        # rainbow gradient
        r = (math.sin(color_phase + phase * 0.8) + 1) / 2
        g = (math.sin(color_phase + 2 + phase * 0.8) + 1) / 2
        b = (math.sin(color_phase + 4 + phase * 0.8) + 1) / 2

        glColor4f(r, g, b, 1.0)
        glVertex3f(x, y, z)
        glColor4f(r, g, b, 0.0)
        glVertex3f(x - 5, y - 5, z + 2)  # smoother trail

        m[0] -= speed * 0.8
        m[1] -= speed * 0.6
        m[2] += speed * 0.2

        if m[0] < -95 or m[1] < -65 or m[2] > -2:
            for _ in range(SPARK_COUNT):
                sparks.append([x, y, z,
                               random.uniform(-1.6, 1.6),
                               random.uniform(-1.6, 1.6),
                               random.uniform(-0.5, 0.5),
                               r, g, b, 1.0])
            reset_meteor(meteors, m)
    glEnd()


# === SPARKS ===
def draw_sparks(sparks):
    glPointSize(2.2)
    glBegin(GL_POINTS)
    alive = []
    for s in sparks:
        x, y, z, vx, vy, vz, r, g, b, life = s
        glColor4f(r, g, b, life)
        glVertex3f(x, y, z)
        s[0] += vx * 0.4
        s[1] += vy * 0.4
        s[2] += vz * 0.4
        s[9] -= 0.03
        if s[9] > 0:
            alive.append(s)
    glEnd()
    sparks[:] = alive


# === BACKGROUND LAYERS ===
def draw_black_background():
    """Opaque deep-black background at the very back."""
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor4f(0.0, 0.0, 0.0, 1.0)
    glVertex3f(-200, -120, -150)
    glVertex3f(200, -120, -150)
    glVertex3f(200, 120, -150)
    glVertex3f(-200, 120, -150)
    glEnd()
    glEnable(GL_DEPTH_TEST)


def draw_nebula_bg(phase):
    glPushMatrix()
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)

    a = 0.16 + 0.08 * math.sin(phase * 0.5)
    b = 0.22 + 0.08 * math.cos(phase * 0.3)
    c = 0.28 + 0.08 * math.sin(phase * 0.7)

    glColor4f(a * 0.7, b * 0.9, c * 1.3, 1.0)
    glVertex3f(-200, -120, -120)
    glColor4f(a, b, c, 1.0)
    glVertex3f(200, -120, -120)
    glColor4f(c, b, a, 1.0)
    glVertex3f(200, 120, -120)
    glColor4f(b, c, a, 1.0)
    glVertex3f(-200, 120, -120)

    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()


# === MAIN ===
def galaxy_screensaver():
    global running_screensaver
    running_screensaver = True

    pygame.init()
    screen = pygame.display.set_mode((0, 0), DOUBLEBUF | OPENGL | FULLSCREEN)
    pygame.mouse.set_visible(False)

    info = pygame.display.Info()
    w, h = info.current_w, info.current_h

    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(75, w / h, 0.1, 300.0)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_POINT_SMOOTH)
    glClearColor(0.0, 0.0, 0.02, 1)

    stars = generate_stars()
    meteors = generate_meteors()
    sparks = []
    clock = pygame.time.Clock()
    phase = 0
    cam_shift = 0

    # Fade-in
    for fade in range(0, 80):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_black_background()
        draw_nebula_bg(fade / 20)
        draw_stars(stars, fade / 10)
        draw_meteors(meteors, fade / 10, sparks)
        pygame.display.flip()
        time.sleep(FADE_SPEED)

    while running_screensaver:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                running_screensaver = False
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                pass

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        cam_shift += 0.002
        glTranslatef(math.sin(cam_shift) * 2, math.cos(cam_shift) * 1.5, 0)
        glRotatef(0.02, 1, 0, 0.3)

        draw_black_background()     # ← drawn first
        draw_nebula_bg(phase)
        draw_stars(stars, phase)
        draw_meteors(meteors, phase, sparks)
        draw_sparks(sparks)
        glPopMatrix()

        phase += ROTATION_SPEED
        pygame.display.flip()
        clock.tick(60)

    # Fade-out
    for fade in range(80, -1, -4):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_black_background()
        draw_nebula_bg(fade / 15)
        draw_stars(stars, fade / 15)
        draw_meteors(meteors, fade / 15, sparks)
        draw_sparks(sparks)
        pygame.display.flip()
        time.sleep(FADE_SPEED / 1.5)

    pygame.quit()
    running_screensaver = False


# === HOTKEY LISTENER ===
def screensaver_listener():
    global screensaver_on, running_screensaver
    print("🌌 Galaxy Nebula Screensaver active. Press Ctrl + Shift + ` to toggle.")

    while True:
        keyboard.wait(TOGGLE_HOTKEY)
        if not screensaver_on:
            screensaver_on = True
            threading.Thread(target=galaxy_screensaver, daemon=True).start()
        else:
            screensaver_on = False
            running_screensaver = False


if __name__ == "__main__":
    try:
        screensaver_listener()
    except KeyboardInterrupt:
        print("Exiting screensaver listener...")
