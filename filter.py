#!/usr/bin/env python3
import numpy as np
import os
import cv2
import argparse
import matplotlib.pyplot as plt
import sys

def mod_z(col: np.array, thresh: float=3.5) -> np.array:
    '''
    Calculates modified z-score.
    Implementation modified from this SO post: https://stackoverflow.com/a/58128516
    '''
    med_col = np.median(col)
    med_abs_dev = np.median(np.abs(col - med_col))
    mod_z = 0.7413 * ((col - med_col) / med_abs_dev)
    mod_z = mod_z[np.abs(mod_z) < thresh]
    return np.abs(mod_z)

def is_rainy_pixel_temporal(intensities, frame_count, thresh):
    # assume gaussian distribution
    mu, sigma = np.mean(intensities), np.std(intensities)

    # modified z score greater than 3.5 count
    mz = mod_z(intensities)
    mz_filtered = mz[mz >= 0]
    outliers = frame_count - len(mz_filtered)
    percent_outliers = outliers/frame_count * 100

    rainy = True if percent_outliers >= thresh else False
    return rainy, mu, sigma, outliers, percent_outliers

def is_rainy_video(cap: cv2.VideoCapture, seq_len: int, thresh: float=2, window=(2,2), show_figs: bool=False, bins: int=15) -> bool:
    '''
    NOTE: if seq_len is negative, all frames will be used
    '''
    # determine properties of video
    frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count = min(frame_count_total, seq_len)
    if seq_len < 0:
        frame_count = frame_count_total
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w_mid = w // 2
    h_mid = h // 2

    # extract window properties
    windw = window[0]
    windh = window[1]
    window_pixels_per_image = windw * windh

    # extract intensities of middle pixel
    intensities = np.zeros((frame_count, window_pixels_per_image))

    for i in range(frame_count):
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        intensities[i] = frame[w_mid:w_mid+windw, h_mid:h_mid+windh].flatten()

    # determine whether rainy from each pixel
    voting = np.zeros(window_pixels_per_image)
    for i in range(window_pixels_per_image):
        voting[i] = is_rainy_pixel_temporal(intensities[:,i], frame_count, thresh)[0]
    
    rainy = False
    if len(voting[voting==True]) >= len(voting[voting==False]):
        rainy = True

    # extract information of a temporal set of pixels with majority vote
    i = np.where(voting == rainy)[0][0]
    _, mu, sigma, outliers, percent_outliers = is_rainy_pixel_temporal(intensities[:,i], frame_count, thresh)

    if show_figs:
        plt.hist(intensities, bins=bins, color='b')
        plt.plot(mu, 0, 'ro')
        plt.plot([mu-sigma, mu+sigma], [0,0], 'o', color="orange")
        plt.show()

    return rainy, mu, sigma, outliers, frame_count, percent_outliers

def main():
    parser = argparse.ArgumentParser(description='filters rainy and non-rainy videos')
    parser.add_argument('folder', help='folder with videos')
    parser.add_argument('-f', '--frames', type=int, default=-1, help='frames to process, defaults to all frames')
    parser.add_argument('-t', '--threshold', type=float, default=2.0, help='threshold for the percentage of outliers to be considered rain drops, default is 2.0 (e.g. 2.0%%)')
    parser.add_argument('-w', '--window', metavar='n', type=int, default=2, help='nxn window of pixels in center of image to process. Default is 2x2.')
    parser.add_argument('--plot', dest='plot_bool', default=False, action='store_true', help='displays plots of the histogram of intensities for each video')
    parser.add_argument('-b', '--bins', type=int, default=15, help='number of bins to display in the histogram plots')
    parser.add_argument('--csv', default=False, action='store_true', help='output csv format')
    args = parser.parse_args()
    folder, plot_bool, frames, threshold, n, bins, csv_bool = args.folder, args.plot_bool, args.frames, args.threshold, args.window, args.bins, args.csv
    window = (n, n)

    if csv_bool:
        print('file,rainy,mean,std,outlier count,total intensities,percent outliers,window')

    for file in sorted(os.listdir(folder)):
        print(f"processing {file}", file=sys.stderr)
        cap = cv2.VideoCapture(os.path.join(folder, file))
        if (int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 0):
            continue
        rainy, mu, sigma, outliers, total_intensities, percent_outliers = is_rainy_video(cap, frames, threshold, window, plot_bool, bins)
        if not csv_bool:
            print(f"\tnumber of outliers: {outliers}, total number of intensities: {total_intensities}, percent outliers: {percent_outliers:.2f}")
            print(f"\tmean: {mu:.2f}, std: {sigma:.2f}")
            print("\trainy") if rainy else print("\tnot rainy")
        else:
            print(f'{file},{rainy},{mu:.2f},{sigma:.2f},{outliers},{total_intensities},{percent_outliers:.2f},{n}x{n}')
            sys.stdout.flush()

if __name__ == "__main__":
    main()