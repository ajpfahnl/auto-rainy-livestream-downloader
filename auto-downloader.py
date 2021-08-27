import dotenv
import os
import requests
import pathlib
import subprocess
import gspread
import time
import datetime

dotenv.load_dotenv()
API_KEYS=os.getenv('API_KEYS').split(",")

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

def download_ydl_ffmpeg(place, url, quality="best", time="00:00:10.00", wait=True, dir="downloads/"):
  '''
  Downloading a video with youtube-dl and ffmpeg

  Parameters
  ----------
  place : str
    video location
  
  url : str
    video URL
  
  quality : str, Default: best
    youtube-dl quality or format of video. See FORMAT SELECTION in the man page.
  
  seconds : int, Default: 10 seconds
    Length of video to download.

  wait : bool, Default: True
    whether to wait for the download process to finish or not. If false, make
    sure to wait for the returned process to finish executing.

  dir : str, Default: downloads/ (in current working directory)
    directory for the video downloads

  Returns
  -------
  Popen subprocess object representing ffmpeg download or youtube-dl process
  if failed to retrieve manifest file.
  '''
  # https://unix.stackexchange.com/questions/230481/how-to-download-portion-of-video-with-youtube-dl-command
  now = datetime.datetime.now()
  time_str = f"{now.year:04}-{now.month:02}-{now.day:02}_{now.hour:02}-{now.minute:02}-{now.second:02}"

  youtube_dl_args = ['youtube-dl', '--youtube-skip-dash-manifest', '-f', quality, '-g', url]
  p_manifest = subprocess.Popen(youtube_dl_args,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
  manifests = p_manifest.communicate()[0].decode().strip().split()
  if len(manifests) == 0:
    print(f"[Error] livestream/video not available for {place} {url}")
    return p_manifest
  manifest = manifests[0]
  download_path = os.path.join(dir, place+"_"+time_str+".mp4")
  print(f"Downloading from: {manifest}")
  print(f"Downloading to: {download_path}")
  ffmpeg_args = ['ffmpeg',
                 "-f", "hls",       # input format is hls
                 '-i', manifest,    # input manifest file link
                 '-t', time,        # time length to record for
                 '-c', "copy",      # copy original codec
                 '-an',             # discard audio
                 download_path]
  p_ffmpeg = subprocess.Popen(ffmpeg_args,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              text=True)
  if wait:
    p_ffmpeg.wait()
  return p_ffmpeg

def find_rainy_places(spreadsheet: gspread.models.Spreadsheet):
  '''
  Return a dictionary of places and their Youtube URLs that currently have rain

  Parameters
  ----------
  spreadsheet : gspread.models.Spreadsheet
    A Google Sheet object
    Each sheet must have three columns: City | Latitude | Longitude | Link
  
  Returns
  -------
  dictionary with the following schema:
    key: 'City' name in the spreadsheet
    value: ['Link' url in spreadsheet, "best" (quality wanted to be passed to youtube-dl)]
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
      city, lat, lon, url = row
      try:
        raining = is_raining(lat, lon, API_KEYS[0])
      except:
        raining = is_raining(lat, lon, API_KEYS[1])
      if raining:
        print(f"\t{city} has rain")
        places[city] = [url, "best"]
  return places

def print_stdout(process):
  '''
  Prints out stdout of a subprocess
  '''
  try:
    for line in process.stdout:
      print(line.rstrip())
  except:
    return

def download(places, tmp_dir="./tmp", final_dir="./downloads"):
  '''
  auto-downloader logic

  Parameters
  ----------
  places : dict
    places dictionary in the same format as find_rainy_places()
  
  tmp_dir : str
    temporary directory where files are downloaded before being moved
    to the permanent final_dir
  
  final_dir : str
    final directory where compeleted downloads are stored
  '''
  tmp_dir_globall = os.path.join(tmp_dir, "*")

  # create temporary directory if it doesn't exist
  pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
  
  # remove any partially downloaded files in the temporary directory
  # if they exist from a previous run
  subprocess.call([f"rm -f {tmp_dir_globall}"], shell=True)

  # create new permanent folder
  now = datetime.datetime.now()
  folder_day_name = f"{now.year:04}-{now.month:02}-{now.day:02}"
  folder_path = os.path.join(final_dir, folder_day_name)
  pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

  # download from livestreams in places dictionary
  processes = [download_ydl_ffmpeg(place,
                                   url, 
                                   quality,
                                   "00:02:00.00", 
                                   wait=False, 
                                   dir=tmp_dir) \
               for place, (url, quality) in places.items()]
  print(f"Attempting download of {len(processes)} video(s).")
  print([p.wait() for p in processes])
  [print_stdout(p) for p in processes]

  # move downloaded videos from temporary directory to permanent directory
  subprocess.call([f"mv {tmp_dir_globall} {folder_path}"], shell=True)


def main():
  '''
  main function

  authenticates with service account information in a json file named
    google-sheet-service-auth.json
  opens spreadsheet titled "webcam-links", finds places with rain, and
    downloads in a continous loop
  '''
  gc = gspread.service_account(filename="google-sheet-service-auth.json")

  while True:
      spreadsheet = gc.open("webcam-links")
      try:
          places = find_rainy_places(spreadsheet)
      except:
          time.sleep(30)
          continue
      download(places)

if __name__ == "__main__":
    main()