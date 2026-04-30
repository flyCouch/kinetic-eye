import json
import sys
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import datetime
import os

# PROJECT METADATA
print(f"--- PROJECT: Kinetic Eye Visualizer ---")
print(f"FILE: {__file__}")
print(f"DATE: {datetime.date.today()}")
print(f"TIME: {datetime.datetime.now().strftime('%H:%M:%S')}")

def update_plot(label, axes, data, r_vals, g_vals, b_vals):
    """Callback function to redraw plots when the switch is toggled."""
    mode = 'RawValue' if label == 'Raw' else 'NormalizedValue'
    y_vals = [d[mode] for d in data]

    # Clear previous plots
    for ax in axes:
        ax.clear()

    # Re-plot R
    axes[0].scatter(r_vals, y_vals, c='red', s=1, alpha=0.5)
    axes[0].set_title('Red Channel')
    axes[0].set_ylabel(label)

    # Re-plot G
    axes[1].scatter(g_vals, y_vals, c='green', s=1, alpha=0.5)
    axes[1].set_title('Green Channel')

    # Re-plot B
    axes[2].scatter(b_vals, y_vals, c='blue', s=1, alpha=0.5)
    axes[2].set_title('Blue Channel')

    plt.draw()

def visualize_scan(json_path):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # Extract static X values
    r_vals = [d['R'] for d in data]
    g_vals = [d['G'] for d in data]
    b_vals = [d['B'] for d in data]

    # Setup Figure and Subplots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(16, 7))
    
    # Display filename across the top
    fig.suptitle(f'File: {os.path.basename(json_path)}', fontsize=16, fontweight='bold')
    
    # Adjust layout to make room for larger buttons
    plt.subplots_adjust(bottom=0.25) 
    axes = [ax1, ax2, ax3]

    # Initial Plot (Normalized)
    update_plot('Normalized', axes, data, r_vals, g_vals, b_vals)

    # Create the larger Switch (RadioButtons)
    # [left, bottom, width, height]
    ax_radio = plt.axes([0.35, 0.05, 0.3, 0.12], facecolor='#f0f0f0')
    radio = RadioButtons(ax_radio, ('Normalized', 'Raw'))

    # Style the buttons to be larger
    for label in radio.labels:
        label.set_fontsize(14)

    # Connect the button to the update function
    radio.on_clicked(lambda label: update_plot(label, axes, data, r_vals, g_vals, b_vals))

    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visualizer_interactive.py <filename.json>")
    else:
        visualize_scan(sys.argv[1])
