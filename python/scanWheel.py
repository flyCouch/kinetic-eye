import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import json
import csv
import tkinter as tk
from tkinter import filedialog
import os
import sys
import math
import datetime

# --- Project Header and Custom Branding ---
__PROJECT__ = "LYTTLE reSearch - Authentic HSL Color Wheel Standard"
__FILE__    = "3dlook26.py"
__DATE__    = "2026-05-17"
__TIME__    = datetime.datetime.now().strftime("%H:%M:%S")

def draw_ui(threshold, max_val=65280, slider_rect=(50, 40, 300, 20)):
    """Draws a flat 2D interactive threshold slider at the bottom of the viewport."""
    x, y, w, h = slider_rect
    
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Render Slider Track Background
    glBegin(GL_QUADS)
    glColor4f(0.15, 0.15, 0.15, 1.0)
    glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h)
    glEnd()
    
    # Render Interactive Red Active Fill
    ratio = min(threshold / max_val, 1.0)
    handle_x = x + (ratio * w)
    glBegin(GL_QUADS)
    glColor4f(0.8, 0.1, 0.1, 1.0)
    glVertex2f(x, y); glVertex2f(handle_x, y); glVertex2f(handle_x, y+h); glVertex2f(x, y+h)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

def draw_wheel_border(center_x, center_y, radius, pan_x, pan_y, zoom, segments=120):
    """Draws a clean boundary ring that shifts and scales with the zoom/pan matrix context."""
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glColor4f(0.3, 0.3, 0.3, 1.0) # Mid-grey boundary ring
    for i in range(segments):
        theta = 2.0 * math.pi * float(i) / float(segments)
        
        # Calculate coordinate point position in baseline space
        bx = radius * math.cos(theta)
        by = radius * math.sin(theta)
        
        # Apply transformation parameters to map cleanly to display pixel targets
        screen_x = center_x + (bx + pan_x) * zoom
        screen_y = center_y + (by + pan_y) * zoom
        glVertex2f(screen_x, screen_y)
    glEnd()
    glLineWidth(1.0)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

def rgb_to_polar_wheel(r, g, b):
    """Transforms raw linear RGB hardware coordinates to authentic radial color wheel layout."""
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    max_c = max(rf, gf, bf)
    min_c = min(rf, gf, bf)
    chroma = max_c - min_c
    
    # 1. Determine pure Hue angle using color theory standards
    if chroma == 0:
        hue_angle = 0.0
    elif max_c == rf:
        hue_angle = ((gf - bf) / chroma) % 6.0
    elif max_c == gf:
        hue_angle = ((bf - rf) / chroma) + 2.0
    else:
        hue_angle = ((rf - gf) / chroma) + 4.0
        
    rad_theta = (hue_angle * 60.0) * (math.pi / 180.0)
    
    # 2. Determine Saturation magnitude (Radius from center core)
    # Pure color sweeps sit on the perimeter edge; balanced gray mixes stay near core.
    saturation = 0.0 if max_c == 0 else (chroma / max_c)
    
    cx = saturation * math.cos(rad_theta)
    cy = saturation * math.sin(rad_theta)
    return cx, cy

def load_data():
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename(filetypes=[("Data files", "*.json *.csv")])
    root.destroy()
    if not path: return []
    try:
        with open(path, 'r') as f:
            if path.endswith('.json'): return json.load(f)
            else: return [row for row in csv.DictReader(f)]
    except Exception as e: print(f"Error loading scan file: {e}"); return []

def main():
    floor, threshold = 0.0, 0.0
    dragging_slider = False
    slider_rect = (50, 40, 300, 20)
    
    # Fixed base wheel definitions
    wheel_center_x = 512
    wheel_center_y = 410
    wheel_base_radius = 260.0
    
    # Interactive navigation metrics
    pan_x, pan_y = 0.0, 0.0
    zoom = 1.0
    
    pygame.init()
    
    # System Initialization Terminal Print
    print("\n" + "="*60)
    print(f"LAB ENGINE:          {__PROJECT__}")
    print(f"ACTIVE SCRIPT:       {__FILE__}")
    print(f"COMPILE DATE:        {__DATE__}")
    print(f"INITIALIZATION TIME: {__TIME__}")
    print("CONTROLS: Scroll Wheel = Zoom | Right-Click & Drag = XY Pan Workspace")
    print("          Click & Drag Slider at bottom left to shift active threshold.")
    print("          Press 'O' to open JSON/CSV scan files.")
    print("="*60 + "\n")
    
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    scan_data = []
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == QUIT: running = False
                elif event.type == KEYDOWN:
                    if event.key == K_o: scan_data = load_data()
                    elif event.key == K_s: 
                        pygame.image.save(pygame.display.get_surface(), f"scan_{datetime.datetime.now().strftime('%H%M%S')}.png")
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        my = 768 - my # OpenGL alignment flip
                        if slider_rect[0] <= mx <= slider_rect[0] + slider_rect[2] and \
                           slider_rect[1] <= my <= slider_rect[1] + slider_rect[3]:
                            dragging_slider = True
                            ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                            threshold = ratio * 65280
                    elif event.button == 4: # Zoom in
                        zoom *= 1.15
                    elif event.button == 5: # Zoom out
                        zoom *= 0.85
                    
                elif event.type == MOUSEBUTTONUP: 
                    if event.button == 1: dragging_slider = False
                    
                elif event.type == MOUSEMOTION:
                    if dragging_slider:
                        mx, _ = event.pos
                        ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                        threshold = ratio * 65280
                    elif pygame.mouse.get_pressed()[2]: # Right-Click Drag XY Panning Action
                        # Scale movement vectors proportionally with the active magnification level
                        pan_x += event.rel[0] / zoom
                        pan_y -= event.rel[1] / zoom

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Establish pure orthographic coordinate workspace canvas
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, 1024, 0, 768, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            if scan_data:
                # Adjust node footprint scale alongside magnification levels dynamically
                glPointSize(max(2.0, min(14.0, 5.0 * zoom)))
                glBegin(GL_POINTS)
                for point in scan_data:
                    try:
                        r, g, b = float(point['R']), float(point['G']), float(point['B'])
                        val = float(point['NormalizedValue'])
                        
                        diff = max(0, val - floor)
                        if diff < threshold: continue
                        
                        # Apply transformation to circular polar representation coordinates
                        cx, cy = rgb_to_polar_wheel(r, g, b)
                        
                        # Project coordinate into spatial canvas tracking window matrix configurations
                        screen_x = wheel_center_x + ((cx * wheel_base_radius) + pan_x) * zoom
                        screen_y = wheel_center_y + ((cy * wheel_base_radius) + pan_y) * zoom
                        
                        # --- 4TH DATUM SCANNER BRIGHTNESS INTERPRETATION ---
                        # Measured scanner value determines illumination luminosity directly
                        brightness_scale = min(1.0, diff / 65280.0)
                        
                        glColor3f((r / 255.0) * brightness_scale, 
                                  (g / 255.0) * brightness_scale, 
                                  (b / 255.0) * brightness_scale)
                        
                        glVertex2f(screen_x, screen_y)
                    except: continue
                glEnd()
                glPointSize(1.0)
            
            # Draw standard enclosing tracking ring and interaction threshold control layouts
            draw_wheel_border(wheel_center_x, wheel_center_y, wheel_base_radius, pan_x, pan_y, zoom)
            draw_ui(threshold, slider_rect=slider_rect)
            
            pygame.display.flip()
            pygame.time.wait(10)
    finally:
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
