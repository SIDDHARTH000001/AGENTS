from trim import trim_video_final, format_timestamp, VideoFileClip
import configparser
import os 
import re

try:
    config = configparser.ConfigParser()
    config.read("config/commonconfig.properties")
    
    _remix_dir = config.get("remixdirectory","_dir").strip()
    vid_frame = int(config.get("remixdirectory","vid_frame").strip())
    print(vid_frame)
except Exception as e:
    print("Error Occured while reading config: ",e)
    

os.makedirs(_remix_dir,exist_ok=True)

def is_digit_ending(filename):
    """Check if the filename ends with digits before the file extension."""
    return re.search(r'\d+\.mp4$', filename) is None

to_convert = [f for f in os.listdir(_remix_dir) if is_digit_ending(f)]

print(f""" Videos found for remix {to_convert}""")

for _videofile in to_convert:
    
    video = VideoFileClip(os.path.join(_remix_dir,_videofile))
    for time in range(0,int(video.duration),vid_frame):
        print(_videofile,format_timestamp(time),end="\r")
        trim_video_final("./remix/"+_videofile,format_timestamp(time),format_timestamp(time+vid_frame),f"""./{_remix_dir}/{_videofile.replace(".mp4","")}_{time}.mp4""")

print("Converstion Done")