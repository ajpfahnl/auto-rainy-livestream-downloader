import dotenv
import os
import requests
import pathlib
import subprocess
import gspread
import time
import datetime
from timezonefinder import TimezoneFinder
import pytz
import astral
from astral.sun import sun

dotenv.load_dotenv()
API_KEYS=os.getenv('API_KEYS').split(",")
TEST=False

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

def print_stdout(process):
	'''
	Prints out stdout of a subprocess
	'''
	try:
		for line in process.stdout:
			print(line.rstrip())
	except:
		return

def download_ydl_ffmpeg(place, url, quality="best", time_length="00:00:10.00", wait=True, dir="downloads/"):
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
		
	time_length : int, Default: 10 seconds
		Length of video to download.
	
	wait : bool, Default: True
		whether to wait for the download process to finish or not. If false, make
		sure to wait for the returned process to finish executing.
	
	dir : str, Default: downloads/ (in current working directory)
		directory for the video downloads
	
	Returns
	-------
	Popen subprocess object representing ffmpeg download or youtube-dl process
	if failed to retrieve manifest file and download path.

	Side Effects
	------------
	files: 
		mp4 video saved to dir
		log file containing output from ffmpeg saved to dir
	'''
	# https://unix.stackexchange.com/questions/230481/how-to-download-portion-of-video-with-youtube-dl-command
	now = datetime.datetime.utcnow()
	time_str = f"{now.year:04}-{now.month:02}-{now.day:02}_{now.hour:02}-{now.minute:02}-{now.second:02}"

	youtube_dl_args = [
		'youtube-dl',
		'--youtube-skip-dash-manifest',
		'-f', quality,
		'-g', url]
	p_manifest = subprocess.Popen(
		youtube_dl_args,
		stdin=subprocess.DEVNULL,
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL)
	manifests = p_manifest.communicate()[0].decode().strip().split()
	if len(manifests) == 0:
		print(f"[Error] livestream/video not available for {place} {url}")
		return p_manifest, ""
	manifest = manifests[0]
	download_path = os.path.join(dir, place+"_"+time_str+".mp4")
	print(f"Downloading to: {download_path}")
	ffmpeg_args = [
		'ffmpeg',
		'-f', 'hls',       # input format is hls
		'-i', manifest,    # input manifest file link
		'-t', time_length, # time length to record for
		'-c', "copy",      # copy original codec
		'-an',             # discard audio
		download_path]
	print("Command:", " ".join(ffmpeg_args))
	log = open(download_path+".log", "x")
	p_ffmpeg = subprocess.Popen(
		ffmpeg_args,
		stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True)
	if wait:
		p_ffmpeg.wait()
	return p_ffmpeg, download_path

def find_rainy_places(spreadsheet: gspread.models.Spreadsheet, daytime=True):
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

			# skip if no latitude or longitude
			if lat == '' or lon == '':
				print("\tlatitude or longitude not specified. Skipping...")
				continue

			# skip if daytime specified and location has no daylight
			if daytime:
				timezone_str = TimezoneFinder().timezone_at(lng=float(lon), lat=float(lat))
				loc = astral.LocationInfo(name='loc', region='region', timezone=timezone_str, latitude=lat, longitude=lon)
				timezone_tzinfo = pytz.timezone(timezone_str)
				s = sun(loc.observer, date=datetime.datetime.now(), tzinfo=loc.timezone)
				hour = datetime.datetime.now(timezone_tzinfo).hour
				if (hour < s['sunrise'].hour) or (hour > s['sunset'].hour):
					print(f"\t{city} is dark")
					continue
			
			# download if location is raining
			try:
				raining = is_raining(lat, lon, API_KEYS[0])
			except:
				raining = is_raining(lat, lon, API_KEYS[1])
			if raining:
				print(f"\t{city} has rain")
				places[city] = [url, "best"]
	return places

def download(places, seconds=10, tmp_dir="./tmp", final_dir="./downloads"):
	'''
	auto-downloader logic

	Parameters
	----------
	places : dict
		places dictionary in the same format as find_rainy_places()
	
	seconds : int
		length of time in seconds for video length
	  
	tmp_dir : str
		temporary directory where files are downloaded before being moved
		to the permanent final_dir

	final_dir : str
		final directory where compeleted downloads are stored
	'''

	# create temporary directory if it doesn't exist
	pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)

	# remove any partially downloaded files in the temporary directory
	# if they exist from a previous run
	# tmp_dir_globall = os.path.join(tmp_dir, "*")
	# subprocess.call([f"rm -f {tmp_dir_globall}"], shell=True)

	# create new permanent folder
	now = datetime.datetime.utcnow()
	folder_day_name = f"{now.year:04}-{now.month:02}-{now.day:02}"
	folder_path = os.path.join(final_dir, folder_day_name)
	pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

	# convert time to string format
	time_length_str = time.strftime('%H:%M:%S', time.gmtime(seconds))

	# download from livestreams in places dictionary
	processes = [
		download_ydl_ffmpeg(
			place,
			url, 
			quality,
			time_length_str, 
			wait=False, 
			dir=tmp_dir) \
		for place, (url, quality) in places.items()]
	
	start_time = time.time()
	print(f"Attempting download of {len(processes)} video(s).")

	# Sometimes downloads go into an infinite loop. To mitigate this,
	# this while loop constantly checks the return codes to see if the
	# processes have completed. If one of the processes exceeds
	# 1.5*seconds+60, the process is killed and its temporary file removed.
	while True:
		time.sleep(1)
		return_codes = [p.poll() for p, _ in processes]
		return_codes_not_None = [r for r in return_codes if r is not None]
		if len(return_codes_not_None) == len(processes):
			break
		elif time.time() > start_time + 1.25*seconds + 60:
			for p, download_path in processes:
				if p.returncode != 0:
					print("Killing...")
					p.kill()
					p.wait()
					subprocess.call([f"rm -f {download_path}"], shell=True)
			break
	
	exit_codes = [p.wait() for p, _ in processes]
	print(exit_codes)

	# move downloaded videos from temporary directory to permanent directory
	for _, download_path in processes:
		subprocess.call([f"mv {download_path} {folder_path}"], shell=True)
	return exit_codes, folder_path


def main():
	'''
	main function

	authenticates with service account information in a json file named
		google-sheet-service-auth.json
	opens spreadsheet titled "webcam-links", finds places with rain, and
		downloads in a continous loop
	'''
	gc = gspread.service_account(filename="google-sheet-service-auth.json")

	# In this pipeline we also want to download a video without rain immediately
	# after it rains. To do this, after every download, we create a dictionary
	# of places to download by updating the previous rainy dictionary with a
	# current rainy places dictionary. If a location had rain in the previous
	# iteration but doesn't have rain now, that location will continue
	# downloading for at least one more iteration.
	places_rainy_old = {}
	while True:
		try:
			spreadsheet = gc.open("webcam-links")
			places_rainy_new = find_rainy_places(spreadsheet)
			places_to_download = places_rainy_old | places_rainy_new
		except:
			print('Error opening spreadsheet or gettng rainy places, waiting 30 seconds...')
			time.sleep(30)
			continue
		exit_codes, _ = download(places_to_download, seconds=120)
		if len(exit_codes) == 0:
			print("No videos to download, waiting 60 seconds...")
			time.sleep(60)
		else:
			places_rainy_old = places_rainy_new

def test():
	'''
	Test function for downloader
	'''
	places = {"TEST": ["https://www.youtube.com/watch?v=xSjORzAWP1Y", "best"]}
	download(places)


if __name__ == "__main__":
	if TEST:
		test()
	else:
		main()