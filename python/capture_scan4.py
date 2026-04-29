import socket
import os
import glob
import datetime
import struct
import csv
import json

# CONFIGURATION
TCP_IP = '127.0.0.1' 
TCP_PORT = 8888 
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')
CAL_FILE = 'calibration.json'

# The struct size is 5 bytes (uint8, uint8, uint8, uint16)
STRUCT_SIZE = 5
STRUCT_FORMAT = '<BBBH'

def setup_logging():
    print("--- PROJECT: Kinetic Eye Pipeline ---")
    print(f"FILE: {__file__}")
    print(f"DATE: {datetime.date.today()}")
    print("Status: Triple-Stream conversion with Normalization enabled.")

def load_calibration():
    """Loads gains from calibration.json or defaults to 1.0 if not found."""
    if os.path.exists(CAL_FILE):
        try:
            with open(CAL_FILE, 'r') as f:
                gains = json.load(f)
                print(f"Calibration loaded: R:{gains.get('r_gain')} G:{gains.get('g_gain')} B:{gains.get('b_gain')}")
                return gains
        except Exception as e:
            print(f"Error loading calibration: {e}. Using defaults.")
    else:
        print("No calibration.json found. Using 1.0 default gains.")
    return {"r_gain": 1.0, "g_gain": 1.0, "b_gain": 1.0}

def get_next_filename():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    existing_files = glob.glob(os.path.join(BASE_DIR, "scan*.bin"))
    max_idx = 0
    for f in existing_files:
        try:
            idx = int(os.path.basename(f).split('scan')[1].split('_')[0])
            if idx > max_idx: max_idx = idx
        except: continue
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(BASE_DIR, f"scan{max_idx + 1:02d}_{timestamp}.bin")

def post_process_scan(bin_path):
    gains = load_calibration()
    print(f"Post-processing: {bin_path}")
    csv_path = bin_path.replace('.bin', '.csv')
    json_path = bin_path.replace('.bin', '.json')
    
    data_records = []
    
    with open(bin_path, 'rb') as f_bin, open(csv_path, 'w', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(['R', 'G', 'B', 'RawValue', 'NormalizedValue'])
        
        while True:
            chunk = f_bin.read(STRUCT_SIZE)
            if len(chunk) < STRUCT_SIZE: break
            
            r, g, b, val = struct.unpack(STRUCT_FORMAT, chunk)
            
            # Normalization: Apply gain based on the dominant channel of the step
            norm_val = val
            if r > g and r > b:
                norm_val = int(val * gains.get('r_gain', 1.0))
            elif g > r and g > b:
                norm_val = int(val * gains.get('g_gain', 1.0))
            elif b > r and b > g:
                norm_val = int(val * gains.get('b_gain', 1.0))
            
            writer.writerow([r, g, b, val, norm_val])
            data_records.append({"R": r, "G": g, "B": b, "Value": norm_val})
            
    with open(json_path, 'w') as f_json:
        json.dump(data_records, f_json, indent=4)
    print(f"Conversion complete: {csv_path} and {json_path}")

def main():
    setup_logging()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    print(f"Connecting to {TCP_IP}:{TCP_PORT}...")
    try:
        sock.connect((TCP_IP, TCP_PORT))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    recording = False
    f = None
    filename = ""
    
    print("Pipeline active. Waiting for START signal...")
    
    while True:
        try:
            data = sock.recv(1024)
            if not data: break
            
            if b'START' in data:
                filename = get_next_filename()
                print(f"START signal received. Saving to: {filename}")
                f = open(filename, 'wb')
                recording = True
                remaining_data = data.split(b'START', 1)[1]
                if remaining_data: 
                    if b'END__' in remaining_data:
                        payload = remaining_data.split(b'END__', 1)[0]
                        f.write(payload)
                    else:
                        f.write(remaining_data)
            
            elif b'END__' in data:
                if recording:
                    payload = data.split(b'END__', 1)[0]
                    if payload: f.write(payload)
                    f.close()
                    print("END signal received. Finalizing files...")
                    post_process_scan(filename)
                    recording = False
                    print("Ready for next scan...")
            
            elif recording:
                f.write(data)
        except KeyboardInterrupt:
            print("\nShutting down pipeline.")
            break

    sock.close()

if __name__ == "__main__":
    main()
