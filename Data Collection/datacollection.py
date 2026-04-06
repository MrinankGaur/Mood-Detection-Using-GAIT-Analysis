import socket
import csv
from typing import Iterator, List, Optional

ESP32_IP = "192.168.4.1"
PORT = 3333

# header used by written CSV and by downstream processors
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


def stream_readings(mood: Optional[str] = None,
                    esp32_ip: str = ESP32_IP,
                    port: int = PORT,
                    max_samples: Optional[int] = None) -> Iterator[List[str]]:
    """Connect to ESP32 and yield rows as lists matching `header`.

    Each yielded row is a list: [timestamp, <28 values...>, mood]
    This generator does NOT write to disk; that's left to callers.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((esp32_ip, port))

    sample = 0
    socket_buffer = ""

    try:
        while True:
            data = s.recv(2048).decode()

            if not data:
                continue

            socket_buffer += data

            while "\n" in socket_buffer:
                line, socket_buffer = socket_buffer.split("\n", 1)

                values = line.split(",")

                if len(values) != 28:
                    continue

                timestamp = format(sample * 0.01, ".2f")

                row = [timestamp] + values + [mood]

                yield row

                sample += 1

                if max_samples is not None and sample >= max_samples:
                    return
    finally:
        try:
            s.close()
        except Exception:
            pass


if __name__ == '__main__':
    # keep previous interactive behavior when run directly
    mood = input("Enter mood label (sad/happy/angry): ")
    iteration = input("Enter iteration number (1/2/3): ")
    filename = "mrinank_" + mood + iteration + ".csv"

    print("Connecting to ESP32...")
    print("Connected!")

    sample = 0
    buffer = []
    socket_buffer = ""

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ESP32_IP, PORT))

        try:
            while True:
                data = s.recv(2048).decode()

                if not data:
                    continue

                socket_buffer += data

                while "\n" in socket_buffer:
                    line, socket_buffer = socket_buffer.split("\n", 1)

                    values = line.split(",")

                    if len(values) != 28:
                        continue

                    timestamp = format(sample * 0.01, ".2f")

                    row = [timestamp] + values + [mood]

                    buffer.append(row)

                    sample += 1

                    # write every 200 rows
                    if len(buffer) >= 200:
                        writer.writerows(buffer)
                        buffer.clear()

                        print("Logged samples:", sample)

                    # close after 12000 readings
                    if sample >= 12000:
                        if buffer:
                            writer.writerows(buffer)
                        print("Reached 12000 samples. Closing connection...")
                        s.close()
                        break
        finally:
            try:
                s.close()
            except Exception:
                pass