import socket
import csv

# =========================
# ESP32 SERVER SETTINGS
# =========================
ESP32_IP = "192.168.4.1"
PORT = 3333

# =========================
# CSV FILE
# =========================
filename = "glove_data.csv"

header = [
"timestamp",

"L1","L2","L3","L4","L5","L6","L7","L8",
"R1","R2","R3","R4","R5","R6","R7","R8",

"acc_x_left","acc_y_left","acc_z_left",
"gyro_x_left","gyro_y_left","gyro_z_left",

"acc_x_right","acc_y_right","acc_z_right",
"gyro_x_right","gyro_y_right","gyro_z_right",

"mood"
]

# =========================
# CONNECT TO ESP32
# =========================
print("Connecting to ESP32...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.4.1",3333))

print("Connected!")

# =========================
# SAMPLE COUNTER
# =========================
sample = 0

# =========================
# OPEN CSV FILE
# =========================
with open(filename,"w",newline="") as file:

    writer = csv.writer(file)
    writer.writerow(header)

    buffer = ""

    while True:

        data = s.recv(1024).decode()

        if not data:
            continue

        buffer += data

        while "\n" in buffer:

            line,buffer = buffer.split("\n",1)

            values = line.split(",")

            if len(values) != 28:
                continue

            # timestamp format: 0.00 0.01 0.02
            timestamp = format(sample*0.01,'.2f')

            mood = ""   # leave empty or label gesture

            row = [timestamp] + values + [mood]

            writer.writerow(row)

            print(row)

            sample += 1