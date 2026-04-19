import socket
import os
import glob
import datetime
import struct

# CONFIGURATION
TCP_IP = '127.0.0.1'
TCP_PORT = 8888  # Change this to match your BT-TCP bridge app port
BASE_DIR = os.path.expanduser('~/projects/kinetic-eye/scans')

def get_next_filename():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    
    # Find existing files to determine increment
    existing_files = glob.glob(os.path.join(BASE_DIR, "scan*.bin"))
    max_idx = 0
    for f in existing_files:
        try:
            # Assumes format: scan(N)_timestamp.bin
            idx = int(f.split('scan')[1].split('_')[0])
            if idx > max_idx:
                max_idx = idx
        except:
            continue
            
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(BASE_DIR, f"scan{max_idx + 1:02d}_{timestamp}.bin")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {TCP_IP}:{TCP_PORT}...")
    sock.connect((TCP_IP, TCP_PORT))
    
    recording = False
    f = None
    
    print("Pipeline active. Waiting for START signal...")
    
    while True:
        data = sock.recv(5) # Read 5-byte chunks as defined in kinetic-eye22.ino 
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
        
        elif recording and f:
            f.write(data)

if __name__ == "__main__":
    main()
