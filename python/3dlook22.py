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
def print_header(floor, gain, threshold):
    print(f"\n--- PROJECT: Kinetic Eye | Spectral Variance Visualizer ---")
    print(f"File: {os.path.basename(__file__)}")
    print(f"Date: {datetime.date.today()} | Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"Controls: [O]pen | [+/-] Stretch | [T/G] Threshold | [S]ave | [Mid-Click] Pan | [Click] Rotate")
    print("----------------------------------------------------------")

def draw_ui(threshold, max_val=65280):
    """Draws a simple 2D slider overlay for the threshold."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1024, 0, 768, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Slider Background
    glBegin(GL_QUADS)
    glColor4f(0.1, 0.1, 0.1, 0.8)
    glVertex2f(20, 20); glVertex2f(220, 20); glVertex2f(220, 40); glVertex2f(20, 40)
    # Slider Handle
    ratio = min(threshold / max_val, 1.0)
    handle_pos = 20 + (ratio * 200)
    glColor4f(0.8, 0.2, 0.2, 1.0)
    glVertex2f(20, 20); glVertex2f(handle_pos, 20); glVertex2f(handle_pos, 40); glVertex2f(20, 40)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def load_data():
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename(filetypes=[("Data files", "*.json *.csv")])
    root.destroy()
    if not path: return []
    data = []
    try:
        if path.endswith('.json'):
            with open(path, 'r') as f: data = json.load(f)
        elif path.endswith('.csv'):
            with open(path, 'r') as f: data = [row for row in csv.DictReader(f)]
    except Exception as e: print(f"Error: {e}")
    return data

def main():
    floor, gain, threshold = 0.0, 0.0005, 0.0
    pygame.init()
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    rotation, pan_x, pan_y, zoom = [0, 0, 0], 0.0, 0.0, 1.0
    scan_data = []
    
    print_header(floor, gain, threshold)
    
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == QUIT: running = False
                elif event.type == KEYDOWN:
                    if event.key == K_o: scan_data = load_data()
                    elif event.key == K_EQUALS or event.key == K_KP_PLUS: floor += 1000
                    elif event.key == K_MINUS or event.key == K_KP_MINUS: floor -= 1000
                    elif event.key == K_t: threshold += 1000 # Increase Filter
                    elif event.key == K_g: threshold = max(0, threshold - 1000) # Decrease Filter
                    elif event.key == K_s: 
                        pygame.image.save(pygame.display.get_surface(), f"scan_{datetime.datetime.now().strftime('%H%M%S')}.png")
                        print("Screenshot saved.")
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 4: zoom *= 1.1
                    elif event.button == 5: zoom *= 0.9
                
                elif event.type == MOUSEMOTION:
                    if pygame.mouse.get_pressed()[1]: 
                        rel = pygame.mouse.get_rel()
                        pan_x += rel[0] * 0.05
                        pan_y -= rel[1] * 0.05

            mouse_pos = pygame.mouse.get_rel()
            if pygame.mouse.get_pressed()[0]:
                rotation[1] += mouse_pos[0] * 0.2
                rotation[0] += mouse_pos[1] * 0.2

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            gluPerspective(45, (display[0]/display[1]), 0.1, 1000.0)
            glTranslatef(pan_x, pan_y, -100.0 / zoom)
            glRotatef(rotation[0], 1, 0, 0)
            glRotatef(rotation[1], 0, 1, 0)

            if scan_data:
                glBegin(GL_LINES)
                for point in scan_data:
                    try:
                        r, g, b = float(point['R']), float(point['G']), float(point['B'])
                        val = float(point['NormalizedValue'])
                        diff = max(0, val - floor)
                        
                        # Filtering Logic
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
            
            draw_ui(threshold)
            pygame.display.flip()
            pygame.time.wait(10)
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
