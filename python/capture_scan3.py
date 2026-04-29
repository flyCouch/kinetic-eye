import socket
import os
import glob
import datetime
import struct
import csv
import json

# CONFIGURATION
# Set this to the COM port or IP depending on your Bluetooth bridge
TCP_IP = '127.0.0.1' 
TCP_PORT = 8888 
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')

# The struct size is 5 bytes (uint8, uint8, uint8, uint16)
STRUCT_SIZE = 5
STRUCT_FORMAT = '<BBBH'

def get_next_filename():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    existing_files = glob.glob(os.path.join(BASE_DIR, "scan*.bin"))
    max_idx = 0
    for f in existing_files:
        try:
            # Extract index from 'scanXX_...'
            idx = int(os.path.basename(f).split('scan')[1].split('_')[0])
            if idx > max_idx: max_idx = idx
        except: continue
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(BASE_DIR, f"scan{max_idx + 1:02d}_{timestamp}.bin")

def post_process_scan(bin_path):
    print(f"Post-processing: {bin_path}")
    csv_path = bin_path.replace('.bin', '.csv')
    json_path = bin_path.replace('.bin', '.json')
    
    data_records = []
    with open(bin_path, 'rb') as f_bin, open(csv_path, 'w', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(['R', 'G', 'B', 'Value'])
        
        while True:
            chunk = f_bin.read(STRUCT_SIZE)
            if len(chunk) < STRUCT_SIZE: break
            
            r, g, b, val = struct.unpack(STRUCT_FORMAT, chunk)
            writer.writerow([r, g, b, val])
            data_records.append({"R": r, "G": g, "B": b, "Value": val})
            
    with open(json_path, 'w') as f_json:
        json.dump(data_records, f_json, indent=4)
    print(f"Conversion complete: CSV and JSON generated.")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {TCP_IP}:{TCP_PORT}...")
    try:
        sock.connect((TCP_IP, TCP_PORT))
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    recording = False
    f = None
    
    print("Pipeline active. Waiting for START signal...")
    
    while True:
        # Read a small chunk to look for signals
        data = sock.recv(1024)
        if not data: break
        
        # Check for START signal in the stream
        if b'START' in data:
            filename = get_next_filename()
            print(f"START signal received. Saving to: {filename}")
            f = open(filename, 'wb')
            recording = True
            # Strip the 'START' string and save the rest of the buffer
            remaining_data = data.split(b'START', 1)[1]
            if remaining_data: f.write(remaining_data)
        
        elif b'END__' in data:
            if recording:
                # Write everything up to the 'END__' signal
                payload = data.split(b'END__', 1)[0]
                if payload: f.write(payload)
                f.close()
                print("END signal received. Closing file.")
                post_process_scan(filename)
                recording = False
                print("Ready for next scan...")
        
        elif recording:
            f.write(data)

if __name__ == "__main__":
    main()
