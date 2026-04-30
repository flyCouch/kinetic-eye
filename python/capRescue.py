import os
from capture_scan4 import post_process_scan # Importing your existing logic

# CONFIGURATION
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')

def run_rescue():
    # Find the most recently created .bin file
    files = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) if f.endswith('.bin')]
    if not files:
        print("No .bin files found in the scans directory.")
        return
        
    latest_file = max(files, key=os.path.getctime)
    print(f"Found latest file: {latest_file}")
    
    # Run the post-processing logic directly
    try:
        post_process_scan(latest_file)
        print("Successfully generated CSV and JSON.")
    except Exception as e:
        print(f"Error during processing: {e}")

if __name__ == "__main__":
    run_rescue()
