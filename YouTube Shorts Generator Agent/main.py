from llmedit import get_graph
import argparse
import configparser
import os
from moviepy import VideoFileClip
import datetime
import sys
import shutil
import random

parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
        '--account',
        '--a',
        type=str,
        required=True,
        help='account name'
    )

parser.add_argument(
        '--name',
        '--n',
        type=str,
        required=False,
        help='Video Path'
    )

args = parser.parse_args()

print("For Account :: ",args.account)

try:
    config = configparser.ConfigParser()
    config.read(f"./config/{args.account}/config.properties")

    APIKey = config.get("AzureCredentials","APIKey").strip()
    Endpoint = config.get("AzureCredentials","Endpoint").strip()
    Deployment = config.get("AzureCredentials","Deployment").strip()
    version = config.get("AzureCredentials","version").strip()
    
    _clip_cut_duration = int(config.get("Trimmer","clipduration").strip())
    overlap = int(config.get("Trimmer","overlap").strip())
    
    
    _remix_dir = config.get("remixdirectory","_dir").strip()
    remix_video_value = config.get("remixdirectory","type").strip()
    remix_video_value = None if remix_video_value=="None" else remix_video_value
        
    list_video_to_convert = []
    _list_video_prestage = []
    _input_video_dir = "./input/"+args.account
    
    archive_path = "./input/"+args.account+"/"+"archive"
    os.makedirs(archive_path,exist_ok=True)

except Exception as e:
    print("Error Occured while reading config: ",e)
    

# if remix_video_value == "random":
#     remix_video_value = os.path.join(_remix_dir,random.choice(os.listdir(_remix_dir))) 
# elif remix_video_value is not None:
if remix_video_value != "random" and remix_video_value is not None:
    remix_video_value = os.path.join(_remix_dir,remix_video_value)

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds}"

def trim_video_final(input_path,start_time,end_time,output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
          
    def time_to_seconds(time_str):
        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
        
    start_seconds = time_to_seconds(start_time)
    end_seconds = time_to_seconds(end_time)
    clip = VideoFileClip(input_path).subclipped(start_seconds,end_seconds)
    clip.write_videofile(output_path)
    clip.close()


if not args.name:
    list_video_to_convert = [
        file for file in os.listdir(_input_video_dir)
        if os.path.isfile(os.path.join(_input_video_dir, file))
    ]
        
else:
    if not os.path.exists(os.path.join(_input_video_dir,args.name)):
        print("Video Path Not Found")
        sys.exit(0)
        
    list_video_to_convert = [args.name]
        
for _videofile in list_video_to_convert:
    video = VideoFileClip(os.path.join(_input_video_dir,_videofile))
    if video.duration > (_clip_cut_duration +3):
        start_time = 0
        for time in range(0, int(video.duration), _clip_cut_duration):
            if time!=0:
                start_time = time - overlap
            end_time = int(min(video.duration,start_time+_clip_cut_duration))
            trim_video_final(os.path.join(_input_video_dir,_videofile),format_timestamp(start_time),format_timestamp(end_time),f"""{_input_video_dir}/{_videofile.replace(".mp4","")}@{start_time}_{end_time}.mp4""")
            _list_video_prestage.append(f"""{_input_video_dir}/{_videofile.replace(".mp4","")}@{start_time}_{end_time}.mp4""")

    else:
        _list_video_prestage.append(os.path.join(_input_video_dir,_videofile))

graph = get_graph(config,args.account)

for video_path in _list_video_prestage:
    try:
        
        if remix_video_value == "random":
            remix_video_value = os.path.join(_remix_dir,random.choice(os.listdir(_remix_dir))) 
        x = graph.invoke(
            {
                "input_video_path":video_path,
                "output_video_path":f"./output/{args.account}",
                "remix":remix_video_value
            }
        )
    except Exception as e:
        print(e)
print(_list_video_prestage)