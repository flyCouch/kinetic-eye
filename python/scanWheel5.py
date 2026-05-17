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
__PROJECT__ = "LYTTLE reSearch - Alpha Chromatic Picker Standard"
__FILE__    = "3dlook26.py"
__DATE__    = "2026-05-17"
__TIME__    = datetime.datetime.now().strftime("%H:%M:%S")

def save_opengl_screenshot(width=1024, height=768):
    """
    Safely captures pixels directly out of the active GPU front rendering buffer
    to prevent blank or black file exports under an accelerated OpenGL context.
    """
    try:
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image_surface = pygame.image.fromstring(data, (width, height), 'RGB')
        image_surface = pygame.transform.flip(image_surface, False, True)
        
        filename = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(image_surface, filename)
        print(f"--> [EXPORT SUCCESS]: Saved clean workspace frame capture to: {filename}")
    except Exception as e:
        print(f"--> [EXPORT ERROR]: Failed to capture GPU surface: {e}")

def draw_ui(threshold, max_val=65280, slider_rect=(50, 40, 300, 20)):
    """Draws the 2D interactive threshold slider at the bottom of the screen."""
    x, y, w, h = slider_rect
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_BLEND) # Keep UI elements fully opaque
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Slider Track - Dark Charcoal
    glBegin(GL_QUADS)
    glColor4f(0.25, 0.25, 0.25, 1.0)
    glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h)
    glEnd()
    
    # Active Slider Fill
    ratio = min(threshold / max_val, 1.0)
    handle_x = x + (ratio * w)
    glBegin(GL_QUADS)
    glColor4f(0.8, 0.1, 0.1, 1.0)
    glVertex2f(x, y); glVertex2f(handle_x, y); glVertex2f(handle_x, y+h); glVertex2f(x, y+h)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

def draw_wheel_border(center_x, center_y, radius, pan_x, pan_y, zoom, segments=120):
    """Draws a boundary ring that maps correctly with pan and zoom movements."""
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_BLEND)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glLineWidth(2.5)
    glBegin(GL_LINE_LOOP)
    glColor4f(0.5, 0.5, 0.5, 1.0) # Medium grey boundary ring
    for i in range(segments):
        theta = 2.0 * math.pi * float(i) / float(segments)
        bx = radius * math.cos(theta)
        by = radius * math.sin(theta)
        
        screen_x = center_x + (bx + pan_x) * zoom
        screen_y = center_y + (by + pan_y) * zoom
        glVertex2f(screen_x, screen_y)
    glEnd()
    glLineWidth(1.0)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

def get_mixed_color_coordinates(r, g, b):
    """
    Maps mixed colors to their true locations on a color picker wheel using 
    three-phase chromatic vector summation.
    """
    rf = r / 255.0
    gf = g / 255.0
    bf = b / 255.0
    
    rx, ry = 1.0, 0.0
    gx, gy = -0.5, 0.8660254
    bx, by = -0.5, -0.8660254
    
    cx = (rf * rx) + (gf * gx) + (bf * bx)
    cy = (rf * ry) + (gf * gy) + (bf * by)
    
    max_val = max(rf, gf, bf)
    min_val = min(rf, gf, bf)
    chroma = max_val - min_val
    
    if max_val == 0 or chroma == 0:
        return 0.0, 0.0
        
    mag = math.sqrt(cx*cx + cy*cy)
    if mag > 0:
        cx = (cx / mag) * chroma
        cy = (cy / mag) * chroma
    else:
        return 0.0, 0.0
        
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
    except Exception as e: 
        print(f"Error loading scan file: {e}")
        return []

def main():
    floor, threshold = 0.0, 0.0
    dragging_slider = False
    slider_rect = (50, 40, 300, 20)
    
    wheel_center_x = 512
    wheel_center_y = 410
    wheel_base_radius = 270.0
    
    pan_x, pan_y = 0.0, 0.0
    zoom = 1.0
    
    pygame.init()
    pygame.display.set_caption(f"{__PROJECT__} - Active Analysis Matrix")
    
    print("\n" + "="*60)
    print(f"LAB SYSTEM:          {__PROJECT__}")
    print(f"SCRIPT REVISION:     {__FILE__}")
    print(f"COMPILE DATE:        {__DATE__}")
    print(f"INITIALIZATION TIME: {__TIME__}")
    print("CONTROLS: Mouse Scroll Wheel = Zoom | Right-Click & Drag = Pan Workspace")
    print("          Click & Drag bottom slider to tune dynamic threshold filter.")
    print("          Press 'O' to open standard JSON/CSV scan files.")
    print("          Press 'S' to export frame capture safely directly from GPU memory.")
    print("="*60 + "\n")
    
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    # Establish background canvas and enable smooth alpha blending pipelines
    glClearColor(0.92, 0.92, 0.92, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    scan_data = []
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == QUIT: running = False
                elif event.type == KEYDOWN:
                    if event.key == K_o: scan_data = load_data()
                    elif event.key == K_s: save_opengl_screenshot(1024, 768)
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        my = 768 - my
                        if slider_rect[0] <= mx <= slider_rect[0] + slider_rect[2] and \
                           slider_rect[1] <= my <= slider_rect[1] + slider_rect[3]:
                            dragging_slider = True
                            ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                            threshold = ratio * 65280
                    elif event.button == 4: zoom *= 1.15
                    elif event.button == 5: zoom *= 0.85
                    
                elif event.type == MOUSEBUTTONUP: 
                    if event.button == 1: dragging_slider = False
                    
                elif event.type == MOUSEMOTION:
                    if dragging_slider:
                        mx, _ = event.pos
                        ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                        threshold = ratio * 65280
                    elif pygame.mouse.get_pressed()[2]: 
                        pan_x += event.rel[0] / zoom
                        pan_y -= event.rel[1] / zoom

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, 1024, 0, 768, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            if scan_data:
                glPointSize(max(4.0, min(24.0, 8.0 * zoom)))
                glBegin(GL_POINTS)
                for point in scan_data:
                    try:
                        r = float(point.get('R', point.get('r', 0)))
                        g = float(point.get('G', point.get('g', 0)))
                        b = float(point.get('B', point.get('b', 0)))
                        
                        val = float(point.get('NormalizedValue', point.get('RawValue', point.get('val', 0))))
                        
                        diff = max(0, val - floor)
                        if diff < threshold: continue
                        
                        cx, cy = get_mixed_color_coordinates(r, g, b)
                        
                        screen_x = wheel_center_x + ((cx * wheel_base_radius) + pan_x) * zoom
                        screen_y = wheel_center_y + ((cy * wheel_base_radius) + pan_y) * zoom
                        
                        # Use the 4th datum scanner value to cleanly map opacity (Alpha)
                        # High intensity = fully saturated and bright; Absorption valley = smoothly transparent
                        alpha_scale = min(1.0, diff / 65280.0)
                        
                        # Colors render at full brightness without being pulled to black
                        glColor4f(r / 255.0, g / 255.0, b / 255.0, alpha_scale)
                        
                        glVertex2f(screen_x, screen_y)
                    except Exception as loop_error:
                        continue 
                glEnd()
                glPointSize(1.0)
            
            draw_wheel_border(wheel_center_x, wheel_center_y, wheel_base_radius, pan_x, pan_y, zoom)
            draw_ui(threshold, slider_rect=slider_rect)
            
            pygame.display.flip()
            pygame.time.wait(10)
            
    except Exception as general_error:
        print(f"\nCRITICAL SHUTDOWN DETECTED: {general_error}")
        input("\nPress ENTER to acknowledge and close terminal window...")
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
