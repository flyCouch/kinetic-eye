import socket
import struct
import json
import os

# CONFIGURATION
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
CAL_FILE = 'calibration.json'
STRUCT_FORMAT = '<BBBH'
STRUCT_SIZE = 5

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {TCP_IP}:{TCP_PORT} for White Balance...")
    sock.connect((TCP_IP, TCP_PORT))
    
    max_r_val, max_g_val, max_b_val = 0, 0, 0
    recording = False
    
    print("Place White Reference Cap. Press BTN on ESP32...")
    
    while True:
        data = sock.recv(1024)
        if not data: break
        
        if b'START' in data:
            recording = True
            print("Calibrating...")
        elif b'END__' in data:
            break
        elif recording:
            # Process chunks to find peaks for each primary color
            for i in range(0, len(data) - (len(data) % STRUCT_SIZE), STRUCT_SIZE):
                chunk = data[i:i+STRUCT_SIZE]
                r, g, b, val = struct.unpack(STRUCT_FORMAT, chunk)
                
                # Capture the peak sensor response for pure channels
                if r > 0 and g == 0 and b == 0: max_r_val = max(max_r_val, val)
                if g > 0 and r == 0 and b == 0: max_g_val = max(max_g_val, val)
                if b > 0 and r == 0 and g == 0: max_b_val = max(max_b_val, val)

    # Calculate Multipliers (Targeting the strongest channel as 1.0)
    peak = max(max_r_val, max_g_val, max_b_val)
    calibration = {
        "r_gain": round(peak / max_r_val, 3) if max_r_val > 0 else 1.0,
        "g_gain": round(peak / max_g_val, 3) if max_g_val > 0 else 1.0,
        "b_gain": round(peak / max_b_val, 3) if max_b_val > 0 else 1.0,
        "calibrated_at": str(os.path.getmtime(CAL_FILE)) if os.path.exists(CAL_FILE) else "new"
    }

    with open(CAL_FILE, 'w') as f:
        json.dump(calibration, f, indent=4)
    print(f"Calibration saved: {calibration}")

if __name__ == "__main__":
    main()
