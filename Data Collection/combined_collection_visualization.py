import socket
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.interpolate import Rbf
import threading

# ===============================
# Configuration
# ===============================
ESP32_IP = "192.168.4.1"
PORT = 3333

# ===============================
# Data Collection Setup
# ===============================
mood = input("Enter mood label (sad/happy/angry): ")
iteration = input("Enter iteration number (1/2/3): ")

filename = "sujal_" + mood + iteration + ".csv"

header = [
"timestamp",
"R1","R2","R3","R4","R5","R6","R7","R8",
"L1","L2","L3","L4","L5","L6","L7","L8",
"acc_x_right","acc_y_right","acc_z_right",
"gyro_x_right","gyro_y_right","gyro_z_right",
"acc_x_left","acc_y_left","acc_z_left",
"gyro_x_left","gyro_y_left","gyro_z_left",
"mood"
]

# ===============================
# Sensor Coordinates
# ===============================
right_foot_coords = np.array([
(284,84),(379,177),(320,154),(272,159),
(362,285),(301,289),(346,364),(294,442)
])

left_foot_coords = np.array([
(140,84),(44,175),(104,153),(152,158),
(62,284),(123,289),(77,363),(130,441)
])

# IMPORTANT: packet sends RIGHT first then LEFT
all_coords = np.vstack((right_foot_coords, left_foot_coords))

# ===============================
# Heatmap Grid
# ===============================
grid_x, grid_y = np.mgrid[0:563:100j, 0:430:100j]

# ===============================
# Plot Setup
# ===============================
plt.ion()
fig, ax = plt.subplots(figsize=(8,10))

is_running = True

def on_close(event):
    global is_running
    is_running = False
    print("Stopping visualization")

fig.canvas.mpl_connect('close_event', on_close)

try:
    bg = mpimg.imread("insoles.png")
    ax.imshow(bg, extent=[0,430,563,0])
except:
    print("insoles.png not found")

heatmap_img = ax.imshow(
np.zeros((100,100)),
extent=[0,430,563,0],
cmap='jet',
alpha=0.6,
vmin=0,
vmax=4096,
interpolation='gaussian'
)

ax.axis("off")

# ===============================
# Shared State
# ===============================
sample_count = 0
lock = threading.Lock()

# ===============================
# Data Collection Thread
# ===============================
def data_collection_thread():

    global sample_count, is_running

    print("Data collection connecting...")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ESP32_IP, PORT))
        print("Data collection connected")
    except Exception as e:
        print("Connection error:", e)
        is_running = False
        return

    sample = 0
    buffer = []
    socket_buffer = ""

    with open(filename,"w",newline="") as f:

        writer = csv.writer(f)
        writer.writerow(header)

        while is_running:

            try:
                data = s.recv(2048).decode()

                if not data:
                    continue

                socket_buffer += data

                while "\n" in socket_buffer:

                    line, socket_buffer = socket_buffer.split("\n",1)

                    values = line.split(",")

                    if len(values) != 28:
                        continue

                    timestamp = format(sample*0.01,".2f")

                    row = [timestamp] + values + [mood]

                    buffer.append(row)

                    sample += 1

                    with lock:
                        sample_count = sample

                    if len(buffer) >= 200:
                        writer.writerows(buffer)
                        buffer.clear()
                        print("Logged samples:", sample)

                    if sample >= 12000:
                        if buffer:
                            writer.writerows(buffer)
                        print("12000 samples reached")
                        is_running = False
                        break

            except Exception as e:
                print("Data thread error:", e)
                break

    s.close()

# ===============================
# Visualization Thread
# ===============================
def visualization_thread():

    global is_running

    print("Visualization connecting...")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((ESP32_IP, PORT))
        print("Visualization connected")
    except Exception as e:
        print("Visualization connection error:", e)
        is_running = False
        return

    buffer = ""

    try:
        while is_running:

            try:
                chunk = s.recv(8192).decode("utf-8")

                if not chunk:
                    break

                buffer += chunk

            except socket.timeout:
                continue

            if "\n" not in buffer:
                continue

            lines = buffer.split("\n")

            if len(lines) < 2:
                continue

            latest_line = lines[-2].strip()
            buffer = lines[-1]

            values = latest_line.split(",")

            if len(values) != 28:
                continue

            try:

                nums = [float(v) for v in values]

                pressure = np.array(nums[:16])

                rbf = Rbf(
                all_coords[:,0],
                all_coords[:,1],
                pressure,
                function='gaussian',
                epsilon=40
                )

                z_grid = rbf(grid_x, grid_y)

                z_grid = np.clip(z_grid,0,4096)

                heatmap_img.set_data(z_grid)

                fig.canvas.draw_idle()

                plt.pause(0.01)

            except:
                continue

    except Exception as e:
        if is_running:
            print("Visualization error:", e)

    s.close()

# ===============================
# Main Execution
# ===============================
print("Starting system")
print("Saving dataset to:", filename)

collection_thread = threading.Thread(
target=data_collection_thread,
daemon=True
)

visual_thread = threading.Thread(
target=visualization_thread,
daemon=True
)

collection_thread.start()
visual_thread.start()

try:
    while is_running:

        with lock:
            if sample_count > 0:
                plt.suptitle(
                f"Samples Collected: {sample_count}/12000",
                fontsize=12
                )

        fig.canvas.draw_idle()
        plt.pause(0.1)

except KeyboardInterrupt:

    print("Stopped by user")
    is_running = False

collection_thread.join(timeout=5)
visual_thread.join(timeout=5)

plt.close("all")

print("Script finished")