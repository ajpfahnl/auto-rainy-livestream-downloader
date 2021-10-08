#!/usr/bin/env python3

import gspread
from pathlib import PosixPath
import argparse
from processor_utils import *
from processor_utils_spanet import *
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser("post-processor for downloaded videos")
    parser.add_argument('-f', '--folder', type=str, default='./downloads', help='parent directory relative to paths of videos specified in Google Sheet')
    args = parser.parse_args()
    downloads_folder = PosixPath(args.folder)

    gc = gspread.service_account(filename="google-sheet-service-auth.json")
    worksheet = gc.open('downloads_first_pass').sheet1
    scene_names, scenes = read_spreadsheet(worksheet, downloads_folder)
    print(f'number of scenes: {len(scenes)}')
    print(f'number of scene names: {len(scene_names)}')

    # Parameters
    params = {
        'save_dir': PosixPath('~/Downloads/new_dataset/').expanduser(), # dir to save SPAN images
    }
    PosixPath(params['save_dir']).mkdir(parents=True, exist_ok=True)

    # used to test SPANet frames to determine which number of frames should be used
    for scene in tqdm(scenes):
        frames = 0
        frames = read_video(scene)
        SPAN_frame = SPAN_gen_single(frames, num_frames=scene['sparsity'])
        clean_frame = read_clean(scene)

        scene_path = PosixPath(params['save_dir'] / scene['name'])
        scene_path.mkdir(parents=True, exist_ok=True)

        scene_sample_path = PosixPath(scene_path / 'sample')
        scene_sample_path.mkdir(parents=True, exist_ok=True)

        scene_name = scene['name']

        Image.fromarray(SPAN_frame.astype(np.uint8)).save(scene_path / (scene_name+'-Webcam-P-000.png'))
        Image.fromarray(clean_frame.astype(np.uint8)).save(scene_path / (scene_name+'-Webcam-C-000.png'))
        for i in tqdm(range(frames.shape[0])):
            Image.fromarray(frames[i].astype(np.uint8)).save(scene_path / (scene_name+f'-Webcam-R-{i:03d}.png'))

        Image.fromarray(SPAN_frame.astype(np.uint8)).save(scene_sample_path / (scene['name']+'-Webcam-P-000.png'))
        Image.fromarray(clean_frame.astype(np.uint8)).save(scene_sample_path / (scene['name']+'-Webcam-C-000.png'))
        Image.fromarray(frames[0].astype(np.uint8)).save(scene_sample_path / (scene['name']+f'-Webcam-R-{i:03d}.png'))
        Image.fromarray(frames[10].astype(np.uint8)).save(scene_sample_path / (scene['name']+f'-Webcam-R-{i:03d}.png'))
        Image.fromarray(frames[20].astype(np.uint8)).save(scene_sample_path / (scene['name']+f'-Webcam-R-{i:03d}.png'))

        for i in tqdm(range(frames.shape[0]), leave=False):
            path_name = scene_path / PosixPath(scene['name']+f'-Webcam-R-{i:03d}.png')
            if not path_name.exists():
                print(f"ruh roh... this file doesn't exist (;_;): {path_name}")

        path_name = scene_path / PosixPath(scene['name']+'-Webcam-P-000.png')
        if not path_name.exists():
            print(f"ruh roh... this file doesn't exist (;_;): {path_name}")
        
        path_name = scene_path / PosixPath(scene['name']+'-Webcam-C-000.png')
        if not path_name.exists():
            print(f"ruh roh... this file doesn't exist (;_;): {path_name}")

if __name__ == "__main__":
    main()