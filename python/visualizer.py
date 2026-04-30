"""
PROJECT: Kinetic Eye - Visualization
FILE: visualize_scan.py
DATE: 2026-04-30
TIME: 12:55:00
"""

import json
import matplotlib.pyplot as plt
import os
import sys

def visualize_scan(json_path):
    print(f"--- PROJECT: Kinetic Eye ---")
    print(f"FILE: {__file__}")
    print(f"DATE: 2026-04-30")
    print(f"TIME: 12:55:00")
    
    # Load the data
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    r = [d['R'] for d in data]
    g = [d['G'] for d in data]
    b = [d['B'] for d in data]
    val = [d['Value'] for d in data]

    # Setup the 3D plot
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Create the scatter plot
    # s=5: point size, c=val: intensity color map
    img = ax.scatter(r, g, b, c=val, cmap='viridis', s=5, alpha=0.6)

    # Labeling
    ax.set_xlabel('Red Intensity')
    ax.set_ylabel('Green Intensity')
    ax.set_zlabel('Blue Intensity')
    ax.set_title(f'Spectral Scan Intensity: {os.path.basename(json_path)}')

    # Add a color bar to show intensity scale
    cbar = fig.colorbar(img, ax=ax, pad=0.1)
    cbar.set_label('Sensor Intensity Value')

    plt.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        visualize_scan(sys.argv[1])
    else:
        print("Usage: python visualize_scan.py <scan_file.json>")
