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
 4. Create API keys at https://api.openweathermap.org for "Current Weather Data". Create a `.env` file with a variable called `API_KEYS` and copy-and-paste the keys separated by a comma. A template can be found [here](.envTEMPLATE).

The following is an example of the format for the __webcam-links__ Google Sheet:
![webcam links](./images/webcam-links.png)

## Logging
At some point I will switch to using the `logging` module, but in the meantime, this script will output information including which locations were found to have rain, the ffmpeg commands used, the download paths, and the return codes of ffmpeg processes. The following is an example snippet of one of my download runs:

```console
$ python3 auto-downloader.py
Region: Central_NA
Region: NW_NA
Region: SW_NA
Region: Southern_NA
	Jonesborough has rain
	Plant_City has rain
	Winter_Garden has rain
Region: Shikoku_Chugoku_JPN
Downloading to: ./tmp/Jonesborough_2021-09-01_12-05-35.mp4
Command: ffmpeg -f hls -i https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1630544736/ei/AM8vYZuRE9Omkgar9ZDIAQ/ip/64.136.131.152/id/ulEKv7LJDxc.1/itag/301/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D299/hls_chunk_host/rr4---sn-a5meknzk.googlevideo.com/playlist_duration/30/manifest_duration/30/vprv/1/playlist_type/DVR/initcwndbps/12810/mh/bc/mm/44/mn/sn-a5meknzk/ms/lva/mv/m/mvi/4/pl/19/dover/11/keepalive/yes/fexp/24001373,24007246/mt/1630522832/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,playlist_duration,manifest_duration,vprv,playlist_type/sig/AOq0QJ8wRQIgXhN1_9IpFB_YMT_aKzXJ91vkBRK00QNzoLALXc81H2sCIQCXBDlsm3NZbs0u_Ar97cHaIFSW1-nC65H2UXc2DOyIUA%3D%3D/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/AG3C_xAwRQIgKzSa0c6DdybVDVVjnW5beL5Yn3GJP6VyjQhNhCYjHigCIQCPq03kznfELitg-kz7bykslU_EaQz8TXDMDE5s3wHZ8g%3D%3D/playlist/index.m3u8 -t 00:02:00 -c copy -an ./tmp/Jonesborough_2021-09-01_12-05-35.mp4
Downloading to: ./tmp/Plant_City_2021-09-01_12-05-38.mp4
Command: ffmpeg -f hls -i https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1630544739/ei/A88vYZeoF8v0kgb_taDYCA/ip/64.136.131.152/id/wLC-Zg33RYc.1/itag/301/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D299/hls_chunk_host/rr5---sn-a5mekned.googlevideo.com/playlist_duration/30/manifest_duration/30/vprv/1/playlist_type/DVR/initcwndbps/12810/mh/Nc/mm/44/mn/sn-a5mekned/ms/lva/mv/m/mvi/5/pl/19/dover/11/keepalive/yes/fexp/24001373,24007246/mt/1630522832/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,playlist_duration,manifest_duration,vprv,playlist_type/sig/AOq0QJ8wRQIgK4ubBYoSI2JtMuE7DhMbVFWCiZT-IZAUkBxnLffTh5ACIQDJSYZq8e9cVxDxm5O20nfvkmVwiOIQyNjUzUxIkYNdvQ%3D%3D/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/AG3C_xAwRQIhAKAni4GDsIzsgIOaZeR0T16sXr2xO2QkZQI_dDtZxAGUAiBJj1dX6eT9ZG5EDa-6iXw4UPa8XiQrIJWOyDfWrq36bw%3D%3D/playlist/index.m3u8 -t 00:02:00 -c copy -an ./tmp/Plant_City_2021-09-01_12-05-38.mp4
Downloading to: ./tmp/Winter_Garden_2021-09-01_12-05-40.mp4
Command: ffmpeg -f hls -i https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1630544741/ei/BM8vYY-6OtT0kgaQnKa4BA/ip/64.136.131.152/id/gFI5ieIpLzU.1/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/hls_chunk_host/rr6---sn-a5mlrn7k.googlevideo.com/playlist_duration/30/manifest_duration/30/vprv/1/playlist_type/DVR/initcwndbps/12810/mh/hw/mm/44/mn/sn-a5mlrn7k/ms/lva/mv/m/mvi/6/pl/19/dover/11/keepalive/yes/fexp/24001373,24007246/mt/1630522832/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,playlist_duration,manifest_duration,vprv,playlist_type/sig/AOq0QJ8wRgIhANtNcAAy2MR9aFgPQxFvyPnXg15m7bEKyJsOPei-bP6iAiEA-1-Y0-iQe9Udvwi-rKvZofoGsxA9vKiebNT56FQSOro%3D/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/AG3C_xAwRQIgNu9xtR7HxPewChUafxmNr_PmE9S974EJZ7dyyxWJ2FECIQDZgkYyYUOkl2k20p0iuxiKDtoCgFWBLPoTvU2ylc1aQQ%3D%3D/playlist/index.m3u8 -t 00:02:00 -c copy -an ./tmp/Winter_Garden_2021-09-01_12-05-40.mp4
Attempting download of 3 video(s).
[0, 0, 0]
Region: Central_NA
Region: NW_NA
Region: SW_NA
Region: Southern_NA
	Jonesborough has rain
	Plant_City has rain
	Winter_Garden has rain
...
```