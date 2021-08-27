# Auto Rainy Livestream Downloader

This program downloads livestream footage from links specified in a Google Sheet if the location has rain. This downloader was used to obtain a rainy dataset for a research project I am working on.

## How to Use
`python3 auto-downloader.py` downloads forever in an infinite loop to a folder called `downloads` in subfolders automatically named with the year, month, and day a video is downloaded. You can also download a single file with `download.sh` which takes the format `./download.sh https://www.youtube.com/watch?v=Nu15hl3Eu7U 00:00:10 out.mp4`.

## Setup
 1. Create a Google Sheet called __webcam-links__ with
    * each sheet is labeled by region 
    * each sheet contains three columns: `City`, `Latitude`, `Longitude`, and `Link` filled in with the corresponding information.
 2. You will need to create a Google _service account_ that has the _Google Sheets API_ enabled. 
    * Share the __webcam-links__ Google Sheet with the Google service account created.
    * You will need to create a key for this service account and download it to a file called `google-sheet-service-auth.json` in this directory. Checkout the template of the file [here](google-sheet-service-authTEMPLATE.json).
 3. Install necessary packages with pip (e.g. `pip install -r requirements.txt`). Note that this was tested on MacOS with Python 3.9.5.
 4. Create API keys on https://api.openweathermap.org. Create a `.env` file with a variable called `API_KEYS` and copy-and-paste the keys separated by a comma. An template can be found [here](.envTEMPLATE).