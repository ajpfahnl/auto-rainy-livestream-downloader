#!/usr/bin/env python3

import gspread
from pathlib import Path
import argparse
from processor_utils import *
from processor_utils_spanet import *
from tqdm import tqdm
from PIL import Image
import time
from datetime import timedelta
import sys

def main():
    parser = argparse.ArgumentParser("post-processor for downloaded videos")
    parser.add_argument('-s', '--sheet', type=str, default='downloads_first_pass', help='name of Google Sheet with metadata')
    parser.add_argument('-i', '--input-folder', type=str, default='./downloads', help='parent directory relative to paths of videos specified in Google Sheet. Default: ./downloads')
    parser.add_argument('-o', '--output-folder', type=str, default='./new-dataset', help='directory of dataset generated. Default: ./new-dataset')
    parser.add_argument('-n', type=int, default=0, help='number of scenes to skip processing')
    args = parser.parse_args()
    sheet_name = args.sheet
    downloads_folder = Path(args.input_folder).expanduser()
    new_dataset_folder = Path(args.output_folder).expanduser()
    num_to_skip = args.n

    gc = gspread.service_account(filename="google-sheet-service-auth.json")
    worksheet = gc.open(sheet_name).sheet1
    scene_names, scenes = read_spreadsheet(worksheet, downloads_folder)
    print(f'number of scenes: {len(scenes)}')
    print(f'number of scene names: {len(scene_names)}')

    # Parameters
    params = {
        'save_dir': new_dataset_folder, # dir to save SPAN images
    }
    new_dataset_folder.mkdir(parents=True, exist_ok=True)

    # used to test SPANet frames to determine which number of frames should be used
    for i, scene in enumerate(scenes):
        if i < num_to_skip:
            continue
        print(f'{i}: {scene["name"]}')
        time_global_start = time.time()
        
        # read video, generate SPAN frame, read clean frame
        time_start = time.time()
        ret, frames = read_video(scene)
        if ret == False:
            print('[ERROR] bad video - no frame count', sys.stderr)
            continue
        print(f'\tRead video: {timedelta(seconds=int(time.time()-time_start))}')
        time_start = time.time()
        SPAN_frame = SPAN_gen_single(frames, num_frames=scene['sparsity'])
        print(f'\tGen SPAN: {timedelta(seconds=int(time.time()-time_start))}')
        clean_frame = read_clean(scene)

        # create folders to write to
        scene_path = Path(params['save_dir'] / scene['name'])
        scene_path.mkdir(parents=True, exist_ok=True)
        scene_sample_path = Path(scene_path / 'sample')
        scene_sample_path.mkdir(parents=True, exist_ok=True)

        # generate dataset
        time_start = time.time()
        scene_name = scene['name']
        Image.fromarray(SPAN_frame.astype(np.uint8)).save(scene_path / (scene_name+'-Webcam-P-000.png'))
        Image.fromarray(clean_frame.astype(np.uint8)).save(scene_path / (scene_name+'-Webcam-C-000.png'))
        for i in range(frames.shape[0]):
            Image.fromarray(frames[i].astype(np.uint8)).save(scene_path / (scene_name+f'-Webcam-R-{i:03d}.png'))

        Image.fromarray(SPAN_frame.astype(np.uint8)).save(scene_sample_path / (scene['name']+'-Webcam-P-000.png'))
        Image.fromarray(clean_frame.astype(np.uint8)).save(scene_sample_path / (scene['name']+'-Webcam-C-000.png'))
        Image.fromarray(frames[20].astype(np.uint8)).save(scene_sample_path / (scene['name']+f'-Webcam-R-020.png'))
        print(f'\tSaving: {timedelta(seconds=int(time.time()-time_start))}')

        for i in tqdm(range(frames.shape[0]), leave=False):
            path_name = scene_path / Path(scene['name']+f'-Webcam-R-{i:03d}.png')
            if not path_name.exists():
                print(f"ruh roh... this file doesn't exist (;_;): {path_name}")

        path_name = scene_path / Path(scene['name']+'-Webcam-P-000.png')
        if not path_name.exists():
            print(f"ruh roh... this file doesn't exist (;_;): {path_name}")
        
        path_name = scene_path / Path(scene['name']+'-Webcam-C-000.png')
        if not path_name.exists():
            print(f"ruh roh... this file doesn't exist (;_;): {path_name}")
        print(f'\tTotal: {timedelta(seconds=int(time.time()-time_global_start))}')

if __name__ == "__main__":
    main()