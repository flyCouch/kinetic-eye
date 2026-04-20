/*
 * PROJECT: Kinetic-Eye Data Pipeline
 * MODULE: Binary to CSV Processor
 * DATE: 2026-04-20
 * TIME: 12:10:00
 */

import socket
import os
import glob
import datetime
import struct
import csv

# CONFIGURATION
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')

def get_next_filename():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    
    existing_files = glob.glob(os.path.join(BASE_DIR, "scan*.bin"))
    max_idx = 0
    for f in existing_files:
        try:
            idx = int(os.path.basename(f).split('scan')[1].split('_')[0])
            if idx > max_idx:
                max_idx = idx
        except:
            continue
            
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(BASE_DIR, f"scan{max_idx + 1:02d}_{timestamp}.bin")

def convert_to_csv(bin_path):
    print(f"Post-processing: Converting {bin_path} to CSV...")
    csv_path = bin_path.replace('.bin', '.csv')
    
    # 'BBB H' matches: uint8_t r, uint8_t g, uint8_t b, uint16_t val
    # '<' ensures little-endian (standard for ESP32/Arduino)
    struct_format = '<BBB H' 
    
    with open(bin_path, 'rb') as bin_file, open(csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['R', 'G', 'B', 'SensorValue'])
        
        while True:
            chunk = bin_file.read(5)
            if not chunk or len(chunk) < 5: break
            
            # Unpack the 5 bytes into a tuple (r, g, b, val)
            unpacked_data = struct.unpack(struct_format, chunk)
            writer.writerow(unpacked_data)
            
    print(f"Conversion complete: {csv_path}")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {TCP_IP}:{TCP_PORT}...")
    sock.connect((TCP_IP, TCP_PORT))
    
    recording = False
    f = None
    
    print("Pipeline active. Waiting for START signal...")
    
    while True:
        data = sock.recv(5)
        if not data: break
        
        if data == b'START':
            filename = get_next_filename()
            print(f"START signal received. Saving to: {filename}")
            f = open(filename, 'wb')
            recording = True
        
        elif data == b'END__':
            if recording:
                print("END signal received. Closing file.")
                f.close()
                recording = False
                convert_to_csv(filename)
        
        elif recording and f:
            f.write(data)

if __name__ == "__main__":
    main()
