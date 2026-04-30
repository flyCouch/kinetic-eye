import socket
import os
import datetime
import struct
import csv
import json

# CONFIGURATION
TCP_IP = '127.0.0.1' 
TCP_PORT = 8888 
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')
CAL_FILE = 'calibration.json'

STRUCT_SIZE = 5
STRUCT_FORMAT = '<BBBH'

def load_calibration():
    if os.path.exists(CAL_FILE):
        try:
            with open(CAL_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"r_gain": 1.0, "g_gain": 1.0, "b_gain": 1.0}

def get_next_filename():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    return os.path.join(BASE_DIR, f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.bin")

def post_process_scan(bin_path, gains):
    print(f"Processing: {bin_path}")
    csv_path = bin_path.replace('.bin', '.csv')
    json_path = bin_path.replace('.bin', '.json')
    data_records = []
    
    with open(bin_path, 'rb') as f_bin, open(csv_path, 'w', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(['R', 'G', 'B', 'RawValue', 'NormalizedValue'])
        while True:
            chunk = f_bin.read(STRUCT_SIZE)
            if not chunk or len(chunk) < STRUCT_SIZE:
                break
            r, g, b, val = struct.unpack(STRUCT_FORMAT, chunk)
            norm = (val * gains['r_gain'] + val * gains['g_gain'] + val * gains['b_gain']) / 3
            writer.writerow([r, g, b, val, norm])
            data_records.append({"R": r, "G": g, "B": b, "RawValue": val, "NormalizedValue": norm})
    with open(json_path, 'w') as f_json:
        json.dump(data_records, f_json, indent=4)
    print(f"Workflow Complete: {csv_path} and {json_path}")

def main():
    print("--- PROJECT: Kinetic Eye V4 (Sync Enabled) ---")
    gains = load_calibration()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((TCP_IP, TCP_PORT))
        print(f"Connected to {TCP_IP}:{TCP_PORT}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    recording = False
    f = None
    filename = ""
    
    print("Waiting for Sync Byte (0xFF)...")
    
    try:
        while True:
            byte = sock.recv(1)
            if not byte: # Connection closed (End of scan)
                if recording:
                    f.close()
                    print("Connection lost. Finalizing file.")
                    post_process_scan(filename, gains)
                    recording = False
                break
            
            # Detect the Sync Anchor (0xFF)
            if byte == b'\xFF':
                if not recording:
                    filename = get_next_filename()
                    print(f"Sync detected. Starting scan: {filename}")
                    f = open(filename, 'wb')
                    recording = True
                
                # Receive the 5 bytes of data
                data = sock.recv(STRUCT_SIZE)
                if len(data) == STRUCT_SIZE:
                    f.write(data)
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
