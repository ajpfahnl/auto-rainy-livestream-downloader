import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import sys

def show_img(img, grey=False):
    plt.figure(figsize=(15, 8))
    if grey:
        plt.imshow(img, cmap='gray', vmin=0, vmax=1)
    else:
        plt.imshow(img)
    plt.show()

def read_spreadsheet(worksheet, folder_path: Path):
    data = worksheet.get_all_values()
    data = np.array(data)
    rows, _ = data.shape

    # currently only loading scenes with both a rainy and clean video in spreadsheet
    scenes = []
    scene_names = {}
    for i in range(1, rows):
        if data[i, 0] != '':
            date = data[i, 0]
        if data[i, 1] != '' and data[i, 2] != '':
            rainy_video_path = Path(folder_path / date / (data[i,1] + '.mp4'))
            clean_video_path = Path(folder_path / date / (data[i,2] + '.mp4'))
            if not rainy_video_path.exists():
                print(f"ruh roh... this rainy vid doesn't exist (;_;): {rainy_video_path}")
                continue
            if not clean_video_path.exists():
                print(f"ruh roh... this clean vid doesn't exist (;_;): {clean_video_path}")
                continue
            if data[i, 5] == '':
                print("No cropping is available...")
                continue
            if data[i, 9] == '':
                print("No timestamps available...")
                continue
            if data[i, 12] == '':
                print("No clean frames available...")
                continue
            if data[i, 13] == '':
                print("No sparsity boolean...")
                continue
            if data[i, 14] == '':
                print("No name...")
                continue
            scene_data = {
                'l' : data[i, 5].astype(np.int),
                'r' : data[i, 6].astype(np.int),
                't' : data[i, 7].astype(np.int),
                'b' : data[i, 8].astype(np.int),
                'rainy_video_path' : rainy_video_path,
                'clean_video_path': clean_video_path,
                'start_frame' : data[i, 9].astype(np.int),
                'end_frame' : data[i, 10].astype(np.int),
                'clean_frame': data[i, 12].astype(np.int),
                'sparsity' : data[i, 13].astype(np.int),
                'name' : data[i, 14]
            }
            print(scene_data)
            scenes.append(scene_data)

            name, right = data[i,14].split("-", 1)
            if name in scene_names.keys():
                scene_names[name] += 1
            else:
                scene_names[name] = 1
    return scene_names, scenes

def read_video(scene) -> tuple[bool, np.ndarray]:
    '''
    returns bool ret:
        True: read successful
        False: read not successful
    '''
    start_frame = scene['start_frame']
    end_frame = scene['end_frame']
    num_frames = end_frame - start_frame
    video_path = scene['rainy_video_path']
    crop_L = scene['l']
    crop_R = scene['r']
    crop_B = scene['b']
    crop_T = scene['t']

    if (crop_R <= crop_L) or (crop_B <= crop_T):
        print('[ERROR] bad crop', sys.stderr)
        return False, np.array([0])
    
    video = cv2.VideoCapture(str(video_path))
    if video.get(cv2.CAP_PROP_FRAME_COUNT) == 0:
        print('[ERROR] bad video - no frame count', sys.stderr)
        return False, np.array([0])

    width_max = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height_max = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    crop_R = width_max if crop_R < 0 else crop_R
    crop_B = height_max if crop_B<0 else crop_B
    height = crop_B - crop_T
    width = crop_R - crop_L

    # skips to first frame
    for i in range(start_frame):
        video.read()
    # create return array
    frames = np.zeros((num_frames, height, width, 3))
    for i in range(num_frames):
        _, frame = video.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = frame[crop_T:crop_B,crop_L:crop_R,:]
        frames[i] = frame
    return True, frames

def read_clean(scene):
    frame_num = scene['clean_frame']
    clean_video_path = scene['clean_video_path']
    video = cv2.VideoCapture(str(clean_video_path))
    crop_L = scene['l']
    crop_R = scene['r']
    crop_B = scene['b']
    crop_T = scene['t']
    for i in range(frame_num):
        video.read()
    _, frame = video.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = frame[crop_T:crop_B,crop_L:crop_R,:]
    return frame

def get_rain_mask(rain, clean):
    rain = rain.astype('int32')
    clean = clean.astype('int32')
    dif = rain-clean
    dif = np.clip(dif, 0, 255)
    # show_img(dif, grey=True)
    return dif

def get_rain_mask_binary(rain, clean):
    rain = rain.astype('int32')
    clean = clean.astype('int32')
    dif = rain - (clean+20) # criterion for rain: rainy > clean + 20 across all three channels

    dif_r = np.clip(dif[:, :, 0], 0, 1)
    dif_g = np.clip(dif[:, :, 1], 0, 1)
    dif_b = np.clip(dif[:, :, 2], 0, 1)

    dif = np.minimum(dif_r, dif_g, dif_b)
    return dif

def preview_crop(image, l=0, r=-1, t=0, b=-1):
    preview_crop = image.copy() # h, w, c
    h = image.shape[0]
    w = image.shape[1]
    print(f'height: {h}')
    print(f'width:  {w}')

    # no params default to no crop
    if r == -1:
        r = w
    if b == -1:
        b = h
    if l == -1:
        l = 0
    if t == -1:
        t = 0

    preview_crop[:,0:l,:] = image[:,0:l,:]/3
    preview_crop[:,r:w,:] = image[:,r:w,:]/3
    preview_crop[0:t,:,:] = image[0:t,:,:]/3
    preview_crop[b:h,:,:] = image[b:h,:,:]/3

    show_img(preview_crop)

def crop_and_save(images, l, r, t, b, save_dir, name):
    if len(images.shape) == 3: # input is single image
        cropped_image = images[t:b,l:r,:]
        Image.fromarray(cropped_image).save(f'{save_dir}/{name}.png')
    else: # input is array of images
        num_images = images.shape[0]
        cropped_images = images[:,t:b,l:r,:]
        for i in range(num_images):
            cropped_image = cropped_images[i]
            Image.fromarray(cropped_image).save(f'{save_dir}/{name}_{i:03d}.png')