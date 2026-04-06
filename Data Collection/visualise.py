import socket
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import sys
from scipy.interpolate import Rbf

# ===============================
# WiFi & Config
# ===============================
HOST, PORT = "192.168.4.1", 3333
BASELINE_R = np.array([0.010,  3.505,  9.362])
BASELINE_L = np.array([0.232, -2.589,  9.760])

# Sensor Positions
right_foot_coords = np.array([(284, 84), (379, 177), (320, 154), (272, 159), (362, 285), (301, 289), (346, 364), (294, 442)])
left_foot_coords = np.array([(140, 84), (44, 175), (104, 153), (152, 158), (62, 284), (123, 289), (77, 363), (130, 441)])
all_coords = np.vstack((right_foot_coords, left_foot_coords))

# ===============================
# HIGH PERFORMANCE RBF PRE-CALCULATION
# ===============================
# We create a transformation matrix so that: heatmap_data = Matrix @ pressure_values
grid_x, grid_y = np.mgrid[0:563:100j, 0:430:100j]
def precompute_rbf_matrix(sources, grid_x, grid_y, epsilon=40):
    # This replaces the slow Rbf() call inside the loop
    rbf_obj = Rbf(sources[:, 0], sources[:, 1], np.zeros(len(sources)), function='gaussian', epsilon=epsilon)
    # Extract the RBF kernel matrix and solve for the grid
    xi = np.column_stack([grid_y.ravel(), grid_x.ravel()])
    di = np.sqrt(((xi[:, None, :] - sources[None, :, :])**2).sum(axis=-1))
    # Gaussian kernel: exp(-(r/epsilon)^2)
    matrix = np.exp(-(di / epsilon)**2)
    return matrix

print("Pre-calculating RBF matrix...")
RBF_MATRIX = precompute_rbf_matrix(all_coords, grid_x, grid_y)

# ===============================
# Setup Plot
# ===============================
plt.ion()
fig = plt.figure(figsize=(14, 10), facecolor='#0d0d1a')

ax_ori_l = fig.add_axes([0.01, 0.25, 0.18, 0.50])
ax_heat  = fig.add_axes([0.20, 0.02, 0.58, 0.96])
ax_ori_r = fig.add_axes([0.80, 0.25, 0.18, 0.50])

# Background Image
try:
    bg = mpimg.imread("insoles.png")
    ax_heat.imshow(bg, extent=[0, 430, 563, 0], zorder=1)
except:
    print("Warning: insoles.png not found."); ax_heat.set_facecolor('black')

heatmap_img = ax_heat.imshow(
    np.zeros((100, 100)), extent=[0, 430, 563, 0],
    cmap='jet', alpha=0.6, vmin=0, vmax=4096, interpolation='gaussian', zorder=2, animated=True
)
ax_heat.axis("off")

def setup_ori_axis(ax, title):
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_aspect('equal')
    ax.set_facecolor('#1a1a2e')
    theta = np.linspace(0, 2 * np.pi, 60)
    ax.plot(np.cos(theta), np.sin(theta), color='#444466', lw=1)
    ax.set_title(title, color='white', fontsize=10)
    ax.axis("off")

setup_ori_axis(ax_ori_l, "Left Foot")
setup_ori_axis(ax_ori_r, "Right Foot")

quiver_r = ax_ori_r.quiver(0, 0, 0, 0, color="#00fff2", scale=1, scale_units='xy', angles='xy', animated=True)
quiver_l = ax_ori_l.quiver(0, 0, 0, 0, color='#00e5ff', scale=1, scale_units='xy', angles='xy', animated=True)
tilt_text_r = ax_ori_r.text(0, -1.25, "", color='#ccccff', ha='center', animated=True)
tilt_text_l = ax_ori_l.text(0, -1.25, "", color='#ccccff', ha='center', animated=True)

# Finalize layout and capture background for blitting
fig.canvas.draw()
background = fig.canvas.copy_from_bbox(fig.bbox)

# ===============================
# Processing Logic
# ===============================
def update_orientation_data(acc, baseline, invert=False):
    delta = acc - baseline
    dx, dy = delta[0] / 9.8, delta[1] / 9.8
    if invert: dx, dy = -dx, -dy
    mag = np.sqrt(dx**2 + dy**2) + 1e-9
    if mag > 0.95: dx, dy = dx * 0.95/mag, dy * 0.95/mag
    tilt = np.degrees(np.arctan2(np.sqrt(delta[0]**2 + delta[1]**2), abs(baseline[2])))
    return dx, dy, tilt

# Socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.setblocking(False) # Non-blocking for smoother feel

buffer = ""
is_running = True

try:
    while is_running:
        try:
            data = s.recv(4096).decode('utf-8')
            if not data: break
            buffer += data
        except BlockingIOError: pass

        if "\n" in buffer:
            lines = buffer.split("\n")
            latest = lines[-2].strip()
            buffer = lines[-1]
            values = latest.split(",")

            if len(values) == 28:
                nums = np.array([float(v) for v in values])
                
                # 1. Fast Heatmap Calculation
                pressure_vals = nums[0:16]
                # Matrix multiplication is much faster than Rbf object call
                z_flat = RBF_MATRIX @ pressure_vals
                z_grid = z_flat.reshape(100, 100)
                
                # 2. Update Orientation
                dxr, dyr, tr = update_orientation_data(nums[16:19], BASELINE_R)
                dxl, dyl, tl = update_orientation_data(nums[22:25], BASELINE_L, invert=True)

                # 3. Blit Rendering (THE FAST PART)
                fig.canvas.restore_region(background)
                
                heatmap_img.set_data(z_grid)
                ax_heat.draw_artist(heatmap_img)

                quiver_r.set_UVC(dxr, dyr); tilt_text_r.set_text(f"Tilt: {tr:.1f}°")
                ax_ori_r.draw_artist(quiver_r); ax_ori_r.draw_artist(tilt_text_r)

                quiver_l.set_UVC(dxl, dyl); tilt_text_l.set_text(f"Tilt: {tl:.1f}°")
                ax_ori_l.draw_artist(quiver_l); ax_ori_l.draw_artist(tilt_text_l)

                fig.canvas.blit(fig.bbox)
                fig.canvas.flush_events()

except KeyboardInterrupt:
    pass
finally:
    s.close()
    plt.close()