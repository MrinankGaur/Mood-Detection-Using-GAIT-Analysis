import numpy as np
import pandas as pd
from scipy.signal import find_peaks

SAMPLING_RATE = 100

WINDOW_SIZE = 400   # 4 sec window
STEP_SIZE = 200     # overlap

PRESSURE_THRESHOLD = 400


def extract_features(window):

    features = {}

    L = window[['L1','L2','L3','L4','L5','L6','L7','L8']].values
    R = window[['R1','R2','R3','R4','R5','R6','R7','R8']].values

    L_flat = L.flatten()
    R_flat = R.flatten()

    # Mean Pressure
    features['mean_pressure_left'] = np.mean(L_flat)
    features['mean_pressure_right'] = np.mean(R_flat)

    # Peak Pressure
    features['peak_pressure_left'] = np.max(L_flat)
    features['peak_pressure_right'] = np.max(R_flat)

    # Variance
    features['pressure_variance_left'] = np.var(L_flat)
    features['pressure_variance_right'] = np.var(R_flat)

    # Heel Toe Ratio
    heel_left = window['L8'].mean()
    heel_right = window['R8'].mean()

    toe_left = window['L1'].mean()
    toe_right = window['R1'].mean()

    features['heel_to_toe_ratio_left'] = np.clip(heel_left/(toe_left+1e-6),0,1.8)
    features['heel_to_toe_ratio_right'] = np.clip(heel_right/(toe_right+1e-6),0,1.8)

    # Contact Area
    features['contact_area_left'] = np.sum(L > PRESSURE_THRESHOLD)
    features['contact_area_right'] = np.sum(R > PRESSURE_THRESHOLD)

    # Impact Force
    features['impact_force_left'] = features['peak_pressure_left'] - features['mean_pressure_left']
    features['impact_force_right'] = features['peak_pressure_right'] - features['mean_pressure_right']

    # IMU Features
    acc_left = window[['acc_x_left','acc_y_left','acc_z_left']].values
    acc_right = window[['acc_x_right','acc_y_right','acc_z_right']].values

    gyro_left = window[['gyro_x_left','gyro_y_left','gyro_z_left']].values
    gyro_right = window[['gyro_x_right','gyro_y_right','gyro_z_right']].values

    features['imu_acc_mean_left'] = np.mean(acc_left)
    features['imu_acc_mean_right'] = np.mean(acc_right)

    features['imu_acc_std_left'] = np.std(acc_left)
    features['imu_acc_std_right'] = np.std(acc_right)

    features['imu_gyro_mean_left'] = np.mean(gyro_left)
    features['imu_gyro_mean_right'] = np.mean(gyro_right)

    features['imu_gyro_std_left'] = np.std(gyro_left)
    features['imu_gyro_std_right'] = np.std(gyro_right)

    # Step Detection
    heel_signal = window['L8'].values + window['R8'].values

    peaks,_ = find_peaks(
        heel_signal,
        height=PRESSURE_THRESHOLD,
        distance=SAMPLING_RATE//2
    )

    if len(peaks) > 1:
        stride_samples = np.diff(peaks)
        stride_times = stride_samples / SAMPLING_RATE

        features['stride_time_mean'] = np.mean(stride_times)
        features['stride_time_std'] = np.std(stride_times)

        window_time = WINDOW_SIZE / SAMPLING_RATE
        steps = len(peaks)

        features['cadence'] = (steps / window_time) * 60

    else:
        features['stride_time_mean'] = 0
        features['stride_time_std'] = 0
        features['cadence'] = 0

    # Step Symmetry
    left_contact = np.sum(window['L8'] > PRESSURE_THRESHOLD)
    right_contact = np.sum(window['R8'] > PRESSURE_THRESHOLD)

    features['step_symmetry'] = left_contact/(right_contact+1e-6)

    # Force Symmetry
    features['force_symmetry'] = features['mean_pressure_left']/(features['mean_pressure_right']+1e-6)

    return features


def process_raw_data(raw_data):

    df = pd.DataFrame(raw_data)

    rows = []

    for i in range(0, len(df) - WINDOW_SIZE, STEP_SIZE):

        window = df.iloc[i : i + WINDOW_SIZE]

        features = extract_features(window)

        rows.append(features)

    final_df = pd.DataFrame(rows)

    # IMPORTANT: maintain SAME order as training
    final_df = final_df[[
        'cadence',
        'stride_time_mean',
        'stride_time_std',
        'mean_pressure_left',
        'mean_pressure_right',
        'peak_pressure_left',
        'peak_pressure_right',
        'pressure_variance_left',
        'pressure_variance_right',
        'heel_to_toe_ratio_left',
        'heel_to_toe_ratio_right',
        'contact_area_left',
        'contact_area_right',
        'impact_force_left',
        'impact_force_right',
        'imu_acc_mean_left',
        'imu_acc_mean_right',
        'imu_acc_std_left',
        'imu_acc_std_right',
        'imu_gyro_mean_left',
        'imu_gyro_mean_right',
        'imu_gyro_std_left',
        'imu_gyro_std_right',
        'step_symmetry',
        'force_symmetry'
    ]]

    return final_df.values.tolist()