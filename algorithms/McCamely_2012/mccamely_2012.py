from scipy.signal import find_peaks
from scipy.signal import detrend, butter, filtfilt, find_peaks
from scipy.integrate import cumtrapz
import math
import statistics
import numpy as np
import pandas as pd
import statistics
import pywt

def mccamely_2012(data):

    # Extract columns to array
    acc_x = np.array(data["accX"]["data"])
    acc_y = np.array(data["accY"]["data"])
    acc_z = np.array(data["accZ"]["data"])

    smooth_rate = 1

    percentagecutoff = round(len(acc_x) * 0.10)
    print(percentagecutoff)
    # Smooth arrays with smooth_rate
    smoothed_acc_x_ar = pd.DataFrame(acc_x).rolling(smooth_rate).mean().values[percentagecutoff:-percentagecutoff]
    smoothed_acc_y_ar = pd.DataFrame(acc_y).rolling(smooth_rate).mean().values[percentagecutoff:-percentagecutoff]
    smoothed_acc_z_ar = pd.DataFrame(acc_z).rolling(smooth_rate).mean().values[percentagecutoff:-percentagecutoff]

    smoothed_acc_x = [x[0] for x in smoothed_acc_x_ar]
    smoothed_acc_y = [x[0] for x in smoothed_acc_y_ar]
    smoothed_acc_z = [x[0] for x in smoothed_acc_z_ar]

    # Calculate RMS
    compound_smoothed_acc = [math.sqrt(smoothed_acc_x[i] ** 2 + smoothed_acc_y[i] ** 2 + smoothed_acc_z[i] ** 2) for i in range(len(smoothed_acc_x))]


    def remove_upper_outliers(data):
        q1 = statistics.quantiles(data, n=4)[0]
        q3 = statistics.quantiles(data, n=4)[2]
        iqr = q3 - q1
        upper_cutoff = q3 + 1.9 * iqr
        return [x for x in data if x <= upper_cutoff]
    

    # Define the sampling frequency, cutoff frequency, and order of the Butterworth filter
    fs = 100 # Sampling frequencyf
    cutoff = 20 # Cutoff frequency
    order = 4 # Order of the Butterworth filter

    # Compute the Butterworth filter coefficients
    w = cutoff / (fs / 2)
    b, a = butter(order, w, btype='lowpass', analog=False)

    # Load accelerometer data and apply the Neilson algorithm to obtain the vertical acceleration and velocity signals

    # Apply the Butterworth filter to the vertical acceleration and velocity signals
    # Detrend the signals to remove any linear trends
    y_filt = filtfilt(b, a, detrend(acc_y))

    # Integrate the vertical velocity signal and detrend the result
    h_int = cumtrapz(y_filt[200:])
    h_int = detrend(h_int)

    # Apply the Gaussian CWT to the negative of the integrated vertical velocity signal to estimate IC events
    ic_coeffs, freqs = pywt.cwt(-h_int, 16, 'gaus1')

    # Apply the Gaussian CWT to the IC signal to estimate FC events
    fc_coeffs, freqs = pywt.cwt(ic_coeffs[0], 16, 'gaus1')

    # Find the indices of the local maxima and minima of the IC and FC signals
    minima_idx = find_peaks(ic_coeffs[0], prominence=1)[0]
    maxima_idx = find_peaks(fc_coeffs[0], prominence=1)[0]

    # Check if the first FC event occurs before the first IC event, and remove it if it does
    if maxima_idx[0] < minima_idx[0]:
        maxima_idx = maxima_idx[1:]

    # Construct a list of step times and stride times using the IC and FC events
    steps = [[ic, fc] for ic, fc in zip(minima_idx, maxima_idx)]

    # Calculate the step time, stride time, and stance time for each step
    step_times = []
    stride_times = []
    stance_times = []

    for i in range(len(steps)-2):
        step_time = (steps[i+1][0] - steps[i][0]) / 100
        stride_time = (steps[i+2][0] - steps[i][0]) / 100
        stance_time = (steps[i+1][1] - steps[i][0]) / 100
        step_times.append(step_time)
        stride_times.append(stride_time)
        stance_times.append(stance_time)


    # Calculate average stride time, step time, and stance time
    average_stride_times = statistics.mean(stride_times)
    average_step_times = statistics.mean(step_times)
    average_stance_times = statistics.mean(stance_times)

    clean_stance_times = remove_upper_outliers(stance_times)
    average_stance_times = statistics.mean(clean_stance_times)

    average_swing_times =  average_stride_times - average_stance_times 
    average_cadence = 60/average_step_times

    return {
        "Stance Time (s)": average_stance_times,
        "Step Time (s)": average_step_times,
        "Stride Time (s)": average_stride_times,
        "Stance (%)": (average_stance_times / average_stride_times) * 100 ,
        "Swing (%)": (average_swing_times /average_stride_times  ) * 100,
        "Cadence": average_cadence
    }