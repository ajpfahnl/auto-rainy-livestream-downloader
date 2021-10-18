#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import cv2
from processor_utils import preview_crop

def main():
    parser = argparse.ArgumentParser('preview crops and other data before processing')
    parser.add_argument('video_path', type=str, help='path to video')
    parser.add_argument('-c', '--crop', type=str, default='', help='crop with format: L,R,T,B')
    parser.add_argument('-f', '--frame', type=int, default=0, help='frame number')
    parser.add_argument('-t', '--seconds', type=float, default=-1, help='number of seconds into video. Supercedes --frame if specified.')
    args = parser.parse_args()

    # check inputs
    video_path = Path(args.video_path)
    video = cv2.VideoCapture(str(video_path))
    if video.get(cv2.CAP_PROP_FRAME_COUNT) == 0:
        print('[ERROR] invalid video')
        exit(1)
    fps = video.get(cv2.CAP_PROP_FPS)
    print(f'FPS: {fps}')

    if args.crop == '':
        crop = (0, -1, 0, -1)
    else:
        crop = tuple([int(d) for d in args.crop.split(',')])
    if len(crop) != 4:
        print('[ERROR] invalid crop', file=sys.stderr)
        exit(1)
    L, R, T, B = crop

    frame_num = args.frame

    if args.seconds != -1:
        frame_num = int(fps*args.seconds)
    print(f'FRAME: {frame_num}')

    # read frame
    for _ in range(frame_num):
        video.read()
    ret, frame = video.read()
    if not ret:
        print('[ERROR] bad frame', file=sys.stderr)
        exit(1)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    preview_crop(frame, L, R, T, B)

if __name__ == '__main__':
    main()