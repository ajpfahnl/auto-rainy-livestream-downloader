#!/usr/bin/env python3

import dotenv
import os
import requests
from pathlib import Path
import subprocess
import gspread
import time
import datetime
from timezonefinder import TimezoneFinder
import pytz
import astral
from astral.sun import sun
import traceback
import argparse

dotenv.load_dotenv()
API_KEYS = os.getenv('API_KEYS').split(",")
TEST = True if os.getenv('TEST').lower() == 'true' else False

def is_raining(lat, lon, api_key):
    '''
    Check if raining at a given latitude and longitude
    
    Parameters
    ----------
    lat : str
        latitude string
        
    lon : str
        longitude string
        
    api_key : str
        api key for api.openweathermap.org
    
    Returns
    -------
    bool : True if location is raining, False if not
    '''
    request_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    r = requests.get(request_url)
    data = r.json()
    if "rain" in data:
        return True
    return False

def find_weather(lat, lon, api_key):
    '''
    Return weather at a given latitude and longitude
    
    Parameters
    ----------
    lat : str
        latitude string
        
    lon : str
        longitude string
        
    api_key : str
        api key for api.openweathermap.org
    
    Returns
    -------
    str : Weather type
    '''
    request_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    r = requests.get(request_url)
    data = r.json()
    return data["weather"][0]["main"].lower()

def download_ydl_ffmpeg(place, url, weather, dir: Path, quality="best", time_length="00:00:10.00", wait=True):
    '''
    Downloading a video with youtube-dl and ffmpeg

    Parameters
    ----------
    place : str
        video location
     
    url : str
        video URL
    
    weather: str
        weather condition at location
      
    dir : Path
        directory for the video downloads

    quality : str, Default: best
        youtube-dl quality or format of video. See FORMAT SELECTION in the man page.
        
    time_length : int, Default: 10 seconds
        Length of video to download.
    
    wait : bool, Default: True
        whether to wait for the download process to finish or not. If false, make
        sure to wait for the returned process to finish executing.
    
    Returns
    -------
    Popen subprocess object representing ffmpeg download or youtube-dl process
    if failed to retrieve manifest file and download path AND download path
    represented as Path object AND associated weather

    Side Effects
    ------------
    files: 
        mp4 video saved to dir
        log file containing output from ffmpeg saved to dir
    '''
    # https://unix.stackexchange.com/questions/230481/how-to-download-portion-of-video-with-youtube-dl-command
    now = datetime.datetime.utcnow()
    time_str = f"{now.year:04}-{now.month:02}-{now.day:02}_{now.hour:02}-{now.minute:02}-{now.second:02}"
    video_name = place+'_'+time_str+'_'+weather
    download_path = dir / (video_name+'.mp4')
    log_path = dir / (video_name+'.log')
    
    # create log
    log = open(log_path, "x")

    # get manifest with youtube-dl
    youtube_dl_args = [
        'youtube-dl',
        '--youtube-skip-dash-manifest',
        '-f', quality,
        '-g', url]
    p_manifest = subprocess.Popen(
        youtube_dl_args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=log)
    manifests = p_manifest.communicate()[0].decode().strip().split()
    if len(manifests) == 0:
        print(f"[Error] livestream/video not available for {place} {url}")
        log.close()
        return p_manifest, download_path
    manifest = manifests[0]

    # download with ffmpeg
    print(f"Downloading to: {download_path}")
    ffmpeg_args = [
        'ffmpeg',
        '-f', 'hls',       # input format is hls
        '-i', manifest,    # input manifest file link
        '-t', time_length, # time length to record for
        '-c', "copy",      # copy original codec
        '-an',             # discard audio
        str(download_path)]
    print("Command:", " ".join(ffmpeg_args))
    p_ffmpeg = subprocess.Popen(
        ffmpeg_args,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT)
    if wait:
        p_ffmpeg.wait()
    
    log.close()
    return p_ffmpeg, download_path

def find_places(spreadsheet: gspread.Spreadsheet, daytime=True):
    '''
    Return a dictionary of places and their Youtube URLs that currently have rain

    Parameters
    ----------
    spreadsheet : gspread.Spreadsheet
        A Google Sheet object
        Each sheet must have four columns: City | Latitude | Longitude | Link
        optionally a fifth column: Not Usable
      
    Returns
    -------
    dictionary with the following schema:
        key: 'City' name in the spreadsheet
        value: ['Link' url in spreadsheet, "best" (quality wanted to be passed to youtube-dl), 'weather' type]
    '''
    # parse spreadsheet data
    metadata = spreadsheet.fetch_sheet_metadata()
    number_of_sheets = len(metadata["sheets"])
    sheets_metadata = metadata["sheets"]

    # fill in places that have rain
    places = {}
    for i in range(number_of_sheets):
        title = sheets_metadata[i]["properties"]["title"]
        print(f"Region: {title}")
        rows = spreadsheet.get_worksheet(i).get_all_values()
        for row in rows[1:]:
            city, lat, lon, url = row[0:4]
            print(f"\t{(city + ':').ljust(20)} ", end='')

            # check for forced skip in "Not Usable" column indicated by a case-insensitive 'X'
            if len(row) > 4:
                if row[4].strip().lower() == 'x':
                    print("SKIP - forced")
                    continue

            # skip if no latitude or longitude
            if lat == '' or lon == '':
                print("SKIP - latitude or longitude not specified")
                continue

            # skip if daytime specified and location has no daylight
            if daytime:
                timezone_str = TimezoneFinder().timezone_at(lng=float(lon), lat=float(lat))
                loc = astral.LocationInfo(name='loc', region='region', timezone=timezone_str, latitude=lat, longitude=lon)
                timezone_tzinfo = pytz.timezone(timezone_str)
                s = sun(loc.observer, date=datetime.datetime.now(), tzinfo=loc.timezone)
                hour = datetime.datetime.now(timezone_tzinfo).hour
                if (hour < s['sunrise'].hour) or (hour > s['sunset'].hour):
                    print(f"SKIP - dark")
                    continue
            
            # download if location is raining
            for api_key in API_KEYS:
                try:
                    weather = find_weather(lat, lon, api_key)
                    break
                except:
                    continue
            print(f"DOWNLOAD - OpenWeatherMap API indicates {weather}")
            places[city] = [url, "best", weather]
    return places

def download(places, seconds=10, tmp_dir=Path('./tmp'), final_dir=Path("./downloads"), timeout=True):
    '''
    auto-downloader logic

    Parameters
    ----------
    places : dict
        places dictionary in the same format as find_rainy_places()
    
    seconds : int
        length of time in seconds for video length
      
    tmp_dir : Path
        temporary directory where files are downloaded before being moved
        to the permanent final_dir

    final_dir : Path
        final directory where compeleted downloads are stored
    
    Returns
    -------
    array of exit codes AND folder path (Path) for the downloads
    '''
    # create temporary directory if it doesn't exist
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # create new permanent folder
    now = datetime.datetime.utcnow()
    folder_day_name = f"{now.year:04}-{now.month:02}-{now.day:02}"
    folder_path = final_dir / folder_day_name
    folder_path.mkdir(parents=True, exist_ok=True)

    # convert time to string format
    time_length_str = time.strftime('%H:%M:%S', time.gmtime(seconds))

    # download from livestreams in places dictionary
    processes = [
        (*download_ydl_ffmpeg(
            place,
            url,
            weather,
            tmp_dir,
            quality,
            time_length_str, 
            wait=False), weather) \
        for place, (url, quality, weather) in places.items()]
    
    start_time = time.time()
    print(f"Attempting download of {len(processes)} video(s).")

    # Sometimes downloads go into an infinite loop. To mitigate this,
    # this while loop constantly checks the return codes to see if the
    # processes have completed. If one of the processes exceeds
    # 1.5*seconds+60, the process is killed and its temporary file removed.
    while True and timeout:
        time.sleep(1)
        return_codes = [p.poll() for p, _, _ in processes]
        return_codes_not_None = [r for r in return_codes if r is not None]
        if len(return_codes_not_None) == len(processes):
            break
        elif time.time() > start_time + 1.25*seconds + 60:
            for p, download_path, _ in processes:
                if p.returncode != 0:
                    print("Killing...")
                    p.kill()
                    p.wait()
                    subprocess.call([f"rm -f '{download_path}'"], shell=True)
            break
    
    exit_codes = [p.wait() for p, _, _ in processes]
    print(exit_codes)

    # move downloaded videos from temporary directory to permanent directory
    # only if successfully downloaded (exit code 0)
    for p, download_path, weather in processes:
        if p.returncode == 0:
            weather_folder_path = final_dir / folder_day_name / weather
            weather_folder_path.mkdir(parents=True, exist_ok=True)
            subprocess.call([f"mv '{download_path}' '{weather_folder_path}'"], shell=True)
    return exit_codes, folder_path


def main():
    '''
    main function

    authenticates with service account information in a json file named
        google-sheet-service-auth.json
    opens spreadsheet titled "webcam-links", finds places with rain, and
        downloads in a continous loop
    '''
    parser = argparse.ArgumentParser(description='downloads rainy videos from a spreadsheet with livestream links')
    parser.add_argument('-df', '--downloads-folder', type=str, default='./downloads/', help='folder to download videos to. Default is ./downloads/')
    parser.add_argument('-nt', '--notimeout', default=False, action='store_true', help='don\'t timeout and kill ffmpeg process')
    parser.add_argument('-s', '--sheet', type=str, default='webcam-links', help='name of Google Sheet to parse livestream information from. Default \'webcam-links\'')
    parser.add_argument('-e', '--extra', type=int, default=1, help='number of extra videos to download after the OpenWeatherMap API says it stops raining. Default 1.')
    args = parser.parse_args()
    downloads_folder = Path(args.downloads_folder).expanduser()
    timeout = not args.notimeout
    if timeout:
        print("ENABLED timeout")
    else:
        print("DISABLED timeout")
    sheet_name = args.sheet
    extra = args.extra

    gc = gspread.service_account(filename="google-sheet-service-auth.json")

    # In this pipeline we also want to download video(s) without rain immediately
    # after it rains. To do this, we use a places_to_download dictionary with the following
    # schema:
    #   key: str place name
    #   value: [str url, str 'best' (quality for youtube-dl), str weather]
    # and a corresponding places_extra dicionaty with the following schema:
    #   key: str place name
    #   value: int extra
    # extra represents the number of times a video should be downloaded after it stops raining
    # according to the rainy API
    places_to_download = {}
    places_extra = {}
    while True:
        try:
            spreadsheet = gc.open(sheet_name)
            places_new = find_places(spreadsheet, daytime=False)
        except:
            print(traceback.format_exc())
            print('Error opening spreadsheet or gettng rainy places, continuing...')
            places_new = {}

        # append the number of times the video should be downloaded after it stops raining
        # add one to account for decrement
        for place in places_new:
            places_extra[place] = extra+1
        
        # update with new, decrement all, remove 0's
        places_to_download.update(places_new)
        for place in list(places_extra):
            places_extra[place] -= 1
            if places_extra[place] == 0:
                del places_to_download[place]
                del places_extra[place]
            elif places_extra[place] < extra:
                print(f'DRY: Downloading {place} {places_extra[place]} more times')

        # download
        exit_codes, _ = download(places_to_download, seconds=120, final_dir=downloads_folder, timeout=timeout)
        if len(exit_codes) == 0:
            print("No videos to download, waiting 60 seconds...")
            time.sleep(60)
        elif 0 not in exit_codes:
            print("All videos failed to download, waiting 60 seconds...")
            time.sleep(60)

def test():
    '''
    Test function for downloader
    '''
    places = {"TEST": ["https://www.youtube.com/watch?v=xSjORzAWP1Y", "best"]}
    download(places, final_dir=Path('~/Downloads/test/').expanduser())


if __name__ == "__main__":
    if TEST:
        test()
    else:
        main()
