# Rainy Livestream Downloader

This program downloads livestream footage from links specified in a Google Sheet if the location has rain. This downloader was used to obtain a rainy dataset for a research project I am working on.

## How to Use
`downloader.py` downloads forever in an infinite loop to a folder, default `downloads`, in subfolders automatically named with the year, month, and day a video is downloaded. You can also download a single file with `download.sh` which takes the format `./download.sh https://www.youtube.com/watch?v=Nu15hl3Eu7U 00:00:10 out.mp4`.
```
usage: downloader.py [-h] [-df DOWNLOADS_FOLDER] [-nt]

downloads rainy videos from a spreadsheet with livestream links

optional arguments:
  -h, --help            show this help message and exit
  -df DOWNLOADS_FOLDER, --downloads-folder DOWNLOADS_FOLDER
                        folder to download videos to. Default is ./downloads/
  -nt, --notimeout      don't timeout and kill ffmpeg process
```

## Setup
This was tested with __Python__ _3.9.6_, __FFmpeg__ _4.4_, and __youtube-dl__ _2021.06.06_. There are known issues with FFmpeg 3.x causing slow downloads.

 1. Create a Google Sheet called __webcam-links__ where
    * each sheet is labeled by region 
    * each sheet contains four columns: `City`, `Latitude`, `Longitude`, and `Link` filled in with the corresponding information.
    * optionally, add a fifth column, `Not Usable`, that, when set to `X` (case insensitive), indicates not to download the video.
 2. You will need to create a Google _service account_ that has the _Google Sheets API_ enabled. 
    * Share the __webcam-links__ Google Sheet with the Google service account created.
    * You will need to create a key for this service account and download it to a file called `google-sheet-service-auth.json` in this directory. Checkout the template of the file [here](google-sheet-service-authTEMPLATE.json).
 3. Install necessary packages either with
    * `pip install -r requirements.txt`
    * `./setup.sh` which sets up a virtual environment and installs necessary packages with pip
 4. Create API keys at https://api.openweathermap.org for "Current Weather Data". Create a `.env` file with a variable called `API_KEYS` and copy-and-paste the keys separated by a comma. A template can be found [here](.envTEMPLATE).

The following is an example of the format for the __webcam-links__ Google Sheet:

![webcam links](./images/webcam-links.png)

## Logging
At some point I will switch to using the `logging` module, but in the meantime, this script will output information including which locations were found to have rain, the ffmpeg commands used, the download paths, and the return codes of ffmpeg processes. The following is an example snippet of one of my download runs:

```console
$ python3 auto-downloader.py
Region: North_America
        Revelstoke:          SKIP - forced
        Skykomish:           SKIP - dark
Region: Japan
        Morioka:             DOWNLOAD - OpenWeatherMap API indicates rain
        Hakodate:            DOWNLOAD - OpenWeatherMap API indicates rain
Region: Europe
        Bad_Langensalza:     DOWNLOAD - OpenWeatherMap API indicates rain
Downloading to: tmp/Morioka_2021-10-05_08-35-08.mp4
Command: ffmpeg -f hls -i https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1633444508/ei/PA5cYfXCLN6QsfIPj62y-AI/ip/64.136.146.253/id/mIqx8S8tQSA.1/itag/95/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D136/hls_chunk_host/rr5---sn-a5mlrn7s.googlevideo.com/playlist_duration/30/manifest_duration/30/vprv/1/playlist_type/DVR/initcwndbps/16360/mh/tl/mm/44/mn/sn-a5mlrn7s/ms/lva/mv/m/mvi/5/pl/19/dover/11/keepalive/yes/fexp/24001373,24007246/mt/1633422751/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,playlist_duration,manifest_duration,vprv,playlist_type/sig/AOq0QJ8wRgIhALUdFNNHwtZFtGxMajlOWG3hRx-cgfQu9F_SxqrtxZrnAiEA0NVUOZ6ucaOkJZNBVnKTe_jVlj4Nh7fnldiJQmVKGnE%3D/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/AG3C_xAwRQIhANHV5_k6TCAX0qCpxxv8RJHzTJNuzXI0n_3C8kIJzl34AiAFtB2fRP5dIAH_cv-PFo-LLZ8YS-CpdLirkW4dMX0EZg%3D%3D/playlist/index.m3u8 -t 00:02:00 -c copy -an tmp/Morioka_2021-10-05_08-35-08.mp4
[Error] livestream/video not available for Hakodate https://www.youtube.com/watch?v=ag2bNNpe3ko
Downloading to: tmp/Bad_Langensalza_2021-10-05_08-35-11.mp4
Command: ffmpeg -f hls -i https://manifest.googlevideo.com/api/manifest/hls_playlist/expire/1633444512/ei/QA5cYa3EKLKRsfIP1oGF8A8/ip/64.136.146.253/id/huTfRXMDFTk.1/itag/96/source/yt_live_broadcast/requiressl/yes/ratebypass/yes/live/1/sgoap/gir%3Dyes%3Bitag%3D140/sgovp/gir%3Dyes%3Bitag%3D137/hls_chunk_host/rr3---sn-a5meknzr.googlevideo.com/playlist_duration/30/manifest_duration/30/vprv/1/playlist_type/DVR/initcwndbps/15290/mh/BN/mm/44/mn/sn-a5meknzr/ms/lva/mv/m/mvi/3/pl/19/dover/11/keepalive/yes/fexp/24001373,24007246/mt/1633422272/sparams/expire,ei,ip,id,itag,source,requiressl,ratebypass,live,sgoap,sgovp,playlist_duration,manifest_duration,vprv,playlist_type/sig/AOq0QJ8wRgIhAMDxlpCB0cz7RuZQAX3ovcqbz5EtflV3IMD3o2iXyItjAiEAyvqq7iIvZh96kPBGLdtuGOq6USdxcCrEeW5FysvMEc0%3D/lsparams/hls_chunk_host,initcwndbps,mh,mm,mn,ms,mv,mvi,pl/lsig/AG3C_xAwRAIgJWCcpDXywB5I7wx_JHGqP9Mu0-p63dtURkn1wH_qDRkCICkDktYEH63unE0vlrh0YSpq67oovecLhS8MklOqDyef/playlist/index.m3u8 -t 00:02:00 -c copy -an tmp/Bad_Langensalza_2021-10-05_08-35-11.mp4
Attempting download of 3 video(s).
[0, 1, 0]
Region: North_America
        Revelstoke:          SKIP - forced
        Skykomish:           SKIP - dark
...
```

## Filtering
NOTE: this is still a WIP

`filter.py` uses modified z-scores to determine outliers in a video that might be indicative of rain. Based on a threshold, a video is classified as rainy or not rainy. The current format for calling the script is as follows:
```
usage: filter.py [-h] [-f FRAMES] [-t THRESHOLD] [-w n] [--plot] [-b BINS] [--csv] folder

filters rainy and non-rainy videos

positional arguments:
  folder                folder with videos

optional arguments:
  -h, --help            show this help message and exit
  -f FRAMES, --frames FRAMES
                        frames to process, defaults to all frames
  -t THRESHOLD, --threshold THRESHOLD
                        threshold for the percentage of outliers to be considered rain drops, default is 2.0 (e.g. 2.0%)
  -w n, --window n      nxn window of pixels in center of image to process. Default is 2x2.
  --plot                displays plots of the histogram of intensities for each video
  -b BINS, --bins BINS  number of bins to display in the histogram plots
  --csv                 output csv format
```
The following is an example of running the script:
```console
$ python3 filter.py ./sample_data --plot
processing Greencastle_2021-09-09_12-58-45_clean.mp4
        number of outliers: 96, total number of intensities: 7200, percent outliers: 1.33
        mean: 120.60, std: 10.11
        not rainy
processing Greencastle_2021-09-09_12-20-14_rainy.mp4
        number of outliers: 366, total number of intensities: 7200, percent outliers: 5.08
        mean: 123.42, std: 14.46
        rainy
```
### clean image histogram:
<img src="./images/Greencastle_clean.png" width="500">

### rainy image histogram:
<img src="./images/Greencastle_rainy.png" width="500">

The following is an example of how to create a csv file:
```console
$ python3 filter.py downloads/2021-09-18 --csv > 2021-09-18.csv
processing Auron_Ski_2021-09-18_15-03-14.mp4
processing Revelstoke_2021-09-18_15-10-19.mp4
processing Geiranger_2021-09-18_16-53-48.mp4
processing Revelstoke_2021-09-18_16-49-10.mp4
$ cat 2021-09-18.csv
file,rainy,mean,std,outlier count,total intensities,percent outliers
Auron_Ski_2021-09-18_15-03-14.mp4,False,129.83,38.29,5,3600,0.14
Revelstoke_2021-09-18_15-10-19.mp4,False,58.56,7.94,0,7200,0.00
Geiranger_2021-09-18_16-53-48.mp4,True,66.91,4.20,150,3600,4.17
Revelstoke_2021-09-18_16-49-10.mp4,False,57.07,5.09,0,7200,0.00
```