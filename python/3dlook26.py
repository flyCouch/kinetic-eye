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

# --- Project Header ---
__FILE__ = "spectral_sphere_v11.py"
__DATE__ = "2026-05-01"
__TIME__ = datetime.datetime.now().strftime("%H:%M:%S")

def draw_ui(threshold, max_val=65280, slider_rect=(50, 50, 300, 20)):
    """Draws 2D UI for the threshold slider with Depth Test disabled."""
    x, y, w, h = slider_rect
    
    # Switch to 2D projection
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Slider Background (Grey)
    glBegin(GL_QUADS)
    glColor4f(0.2, 0.2, 0.2, 1.0)
    glVertex2f(x, y); glVertex2f(x+w, y); glVertex2f(x+w, y+h); glVertex2f(x, y+h)
    glEnd()
    
    # Slider Handle (Red) - Granulated
    ratio = min(threshold / max_val, 1.0)
    handle_x = x + (ratio * w)
    glBegin(GL_QUADS)
    glColor4f(0.8, 0.2, 0.2, 1.0)
    glVertex2f(x, y); glVertex2f(handle_x, y); glVertex2f(handle_x, y+h); glVertex2f(x, y+h)
    glEnd()
    
    # Restore 3D
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

def load_data():
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename(filetypes=[("Data files", "*.json *.csv")])
    root.destroy()
    if not path: return []
    try:
        with open(path, 'r') as f:
            if path.endswith('.json'): return json.load(f)
            else: return [row for row in csv.DictReader(f)]
    except Exception as e: print(f"Error loading: {e}"); return []

def main():
    floor, gain, threshold = 0.0, 0.0005, 0.0
    dragging = False
    slider_rect = (50, 50, 300, 20) # X, Y, W, H
    
    pygame.init()
    
    # Print the project header to the console on launch
    print("\n" + "="*60)
    print(f"LAUNCHING ARCHIVE FILE: {__FILE__}")
    print(f"COMPILE BASE DATE:      {__DATE__}")
    print(f"INITIALIZATION TIME:    {__TIME__}")
    print("CONTROLS: Left-Click & Drag = Orbit | Right-Click & Drag = Pan | Scroll = Zoom")
    print("          Press 'O' to open JSON/CSV | '+' or '-' to adjust floor")
    print("="*60 + "\n")
    
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    rotation, pan_x, pan_y, zoom = [0, 0, 0], 0.0, 0.0, 1.0
    scan_data = []
    
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == QUIT: running = False
                elif event.type == KEYDOWN:
                    if event.key == K_o: scan_data = load_data()
                    elif event.key in (K_EQUALS, K_KP_PLUS): floor += 1000
                    elif event.key in (K_MINUS, K_KP_MINUS): floor -= 1000
                    elif event.key == K_s: 
                        pygame.image.save(pygame.display.get_surface(), f"scan_{datetime.datetime.now().strftime('%H%M%S')}.png")
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        my = 768 - my # Flip for OpenGL
                        if slider_rect[0] <= mx <= slider_rect[0] + slider_rect[2] and \
                           slider_rect[1] <= my <= slider_rect[1] + slider_rect[3]:
                            dragging = True
                            ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                            threshold = ratio * 65280
                    elif event.button == 4: zoom *= 1.1
                    elif event.button == 5: zoom *= 0.9
                    
                elif event.type == MOUSEBUTTONUP: 
                    if event.button == 1: dragging = False
                elif event.type == MOUSEMOTION:
                    if dragging:
                        mx, _ = event.pos
                        ratio = max(0, min(1, (mx - slider_rect[0]) / slider_rect[2]))
                        threshold = ratio * 65280
                    elif pygame.mouse.get_pressed()[0]: 
                        # Left-Click & Drag outside the slider handles 3D Rotation
                        rotation[1] += event.rel[0] * 0.5
                        rotation[0] += event.rel[1] * 0.5
                    elif pygame.mouse.get_pressed()[2]: 
                        # Right-Click & Drag handles smooth X/Y Panning
                        pan_x += event.rel[0] * 0.05
                        pan_y -= event.rel[1] * 0.05

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            gluPerspective(45, (display[0]/display[1]), 0.1, 1000.0)
            glTranslatef(pan_x, pan_y, -100.0 / zoom)
            glRotatef(rotation[0], 1, 0, 0); glRotatef(rotation[1], 0, 1, 0)

            if scan_data:
                glBegin(GL_LINES)
                for point in scan_data:
                    try:
                        r, g, b = float(point['R']), float(point['G']), float(point['B'])
                        val = float(point['NormalizedValue'])
                        diff = max(0, val - floor)
                        if diff < threshold: continue
                        
                        dx, dy, dz = r - 127.5, g - 127.5, b - 127.5
                        mag = math.sqrt(dx**2 + dy**2 + dz**2)
                        if mag > 0:
                            ux, uy, uz = dx/mag, dy/mag, dz/mag
                            tx, ty, tz = ux * (diff * gain), uy * (diff * gain), uz * (diff * gain)
                            glColor3f(r/255.0, g/255.0, b/255.0)
                            glVertex3f(0, 0, 0); glVertex3f(tx, ty, tz)
                    except: continue
                glEnd()
            
            draw_ui(threshold, slider_rect=slider_rect)
            pygame.display.flip()

            pygame.time.wait(10)
    finally:
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
