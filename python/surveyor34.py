# =================================================================
# PROJECT: Kinetic Eye Brain
# FILE: surveyor32_manual_first.py
# DATE: 2026-04-17 | TIME: 14:15
# ! SECURITY NOTE: API KEY IS HARDCODED BELOW !
# =================================================================

import requests
import os
import json
import time
import glob
import select
import sys

# --- CONFIG ---
API_KEY = "pl@ntnet"
CAMERA_DIR = "/sdcard/DCIM/Camera/kinetic-eye"
B_DIR = "/sdcard/kinetic-eye"
D_PATH = os.path.join(B_DIR, "foraging_history.json")
API_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&no-reject=true"

# Bluetooth Serial Path
BT_SERIAL_PATH = "/dev/rfcomm0"

def setup_print():
    """Project Header Prints as per Kinetic Eye Protocol."""
    print(f"\n--- KINETIC EYE SYSTEM BOOT ---")
    print(f"Project Name: Kinetic Eye Brain")
    print(f"File: {os.path.basename(__file__)}")
    print(f"Compile Date: 2026-04-17")
    print(f"Baud Rate: 115200 (Logical)")
    print(f"Status: MANUAL-FIRST VERIFICATION MODE")
    print(f"----------------------------------\n")

def ensure_environment():
    for folder in [CAMERA_DIR, B_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

def get_latest_photo():
    files = glob.glob(f'{CAMERA_DIR}/*.jpg')
    if not files:
        files = glob.glob('/sdcard/DCIM/Camera/*.jpg')
    return max(files, key=os.path.getctime) if files else None

def select_organ():
    options = ["leaf", "flower", "bark", "fruit", "stem"]
    print("\n--- [ TARGET SELECTION ] ---")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt.capitalize()}")
    choice = input("\n>>> Select Organ Number (Default 1): ").strip()
    idx = int(choice) - 1 if choice.isdigit() else 0
    return options[idx] if 0 <= idx < 5 else "leaf"

def run_mission():
    ensure_environment()
    setup_print()
    
    print("[!] MODE: Manual Input Active.")
    print("  [ENTER] - Proceed with standard photo analysis.")
    print("  [V]     - Wait for Staff Verification (RGB/UV Sweep).")
    
    mode_choice = input("\n>>> Choice: ").strip().lower()

    staff_triggered = False
    if mode_choice == 'v':
        print("[*] SYSTEM: Awaiting Staff Trigger via Bluetooth...")
        # Listening loop for the Staff 'Boss' signal
        while True:
            if os.path.exists(BT_SERIAL_PATH):
                try:
                    with open(BT_SERIAL_PATH, "r") as bt:
                        line = bt.readline().strip()
                        if "STAFF_START" in line:
                            print("\n[!] STAFF SIGNAL: 18-Second Scan Initiated!")
                            staff_triggered = True
                            break
                except Exception:
                    pass
            # Safety break if user changes mind
            if select.select([sys.stdin], [], [], 0.1)[0]:
                sys.stdin.readline()
                print("[i] Cancelled hardware wait. Switching to manual.")
                break
    else:
        print("[*] MODE: Standard Manual Analysis.")

    # Restoring v27 logic: Photo capture prompt
    input("\n>>> Press [ENTER] once photo is ready in gallery...")

    p_path = get_latest_photo()
    if not p_path:
        print("[!] ERROR: No visual data found.")
        return

    chosen_organ = select_organ()
    
    # Only wait if the staff was actually engaged for verification
    if staff_triggered:
        print("[*] SYNC: Waiting 18s for spectral hardware workers...")
        time.sleep(18)

    # API Identification Logic
    print(f"\n[*] ACTION: Processing {os.path.basename(p_path)} as '{chosen_organ}'")
    try:
        with open(p_path, 'rb') as img:
            files = [('images', (os.path.basename(p_path), img, 'image/jpeg'))]
            data = {'organs': [chosen_organ]}
            r = requests.post(API_URL, files=files, data=data, timeout=30)
        
        if r.status_code == 200:
            res = r.json()
            if res.get('results'):
                top = res['results'][0]
                species = top.get('species', {}).get('scientificNameWithoutAuthor', "Unknown")
                score = top.get('score', 0.0) * 100
                print(f"\n[!] RESULT: {species} ({score:.1f}%)")
                
                # Log Entry
                log_data = {
                    "timestamp": time.ctime(),
                    "organ": chosen_organ,
                    "species": species,
                    "confidence": round(score, 2),
                    "verified_by_staff": staff_triggered,
                    "file": os.path.basename(p_path)
                }
                with open(D_PATH, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
                    print(f"[*] LOGGED: Entry synced to {D_PATH}")
            else:
                print("[i] No match found.")
    except Exception as e:
        print(f"[!] System Failure: {e}")

if __name__ == "__main__":
    run_mission()
