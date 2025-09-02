import os
import datetime
from moviepy import *
import moviepy as mp 
import speech_recognition as sr 
import sys
import whisper
from pathlib import Path
import time
import subprocess
import warnings
from moviepy.video import fx as vfx
import numpy as np
import configparser
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.load.*")
warnings.filterwarnings("ignore", category=UserWarning, message="FP16 is not supported on CPU")


class Editor:
    def __init__(self,account_name):          
        try:
            config = configparser.ConfigParser()
            config.read(f"config/{account_name}/config.properties")
            
            # ___________________________________ Subtitles
            self.FONT_DIR = config.get("Subtitles","font_dir").strip()
            self._subtitle_color = config.get("Subtitles","color").strip()
            self.subtitle_font_size = int(config.get("Subtitles","font_size").strip())
            self.subtitle_font_window = int(config.get("Subtitles","font_window").strip())
            self._sub_stroke_width = int(config.get("Subtitles","stroke_width").strip())
            
            x_sub_pos, y_sub_pos = config.get("Subtitles","x_pos").strip(), config.get("Subtitles","y_pos").strip()
            self.x_sub_pos = int(x_sub_pos) if len(x_sub_pos)<=4 else x_sub_pos
            self.y_sub_pos = int(y_sub_pos) if len(y_sub_pos)<=4 else y_sub_pos
            
            
            # ____________________________________ logo
            self.logo = os.path.join(f"config/{account_name}",config.get("Logo","logo").strip())
            if not os.path.exists(self.logo):
                print("Logo path not Found")
                sys.exit(1)
            self._logo_height = int(config.get("Logo","height").strip())
            self._logo_opacity = float(config.get("Logo","opacity").strip()) 
            _x_pos_logo, _y_pos_logo = config.get("Logo","x_pos").strip(), config.get("Logo","y_pos").strip()
            self._x_pos_logo = int(_x_pos_logo) if len(_x_pos_logo)<=4 else _x_pos_logo
            self._y_pos_logo = int(_y_pos_logo) if len(_y_pos_logo)<=4 else _y_pos_logo


        except Exception as e:
            print("Error Occured while reading config: ",e)
            

    
    def trim_video_final(self,input_path,start_time,end_time,output_path):
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


    def concatenate_videos(self,video_paths, output_path, method="compose"):
        """
        Concatenate multiple videos into a single video file.
        
        Args:
            video_paths (list): List of paths to input video files
            output_path (str): Path for the output video
            method (str): Method of concatenation ("compose" or "reduce")
                        "compose" is more precise but slower
                        "reduce" is faster but may have quality loss
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load all video clips
            clips = []
            for path in video_paths:
                clip = VideoFileClip(path)
                clips.append(clip)
                
            # Concatenate the clips
            final_clip = concatenate_videoclips(clips, method=method)
            
            # Write the output file
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            # Clean up
            final_clip.close()
            for clip in clips:
                clip.close()
                
            return True
            
        except Exception as e:
            print(f"Error concatenating videos: {str(e)}")
            
            try:
                if 'final_clip' in locals():
                    final_clip.close()
                for clip in clips:
                    clip.close()
            except:
                pass
                
            return False


    def add_video_effects(self,clips, effect_name="fade", duration=1.0):
        """
        Add transition effects between video clips
        
        Args:
            clips (list): List of VideoFileClip objects
            effect_name (str): Type of effect ('fade', 'slide', 'zoom', 'rotate', 'crossfade')
            duration (float): Duration of the effect in seconds
        """
        final_clips = []
        
        for i, clip in enumerate(clips):
            if effect_name == "fade":
                clip =CompositeVideoClip([vfx.FadeIn(duration).apply(clip)])
            elif effect_name == "blink":
                clip =CompositeVideoClip([vfx.Blink(2,5).apply(clip)])
            
            elif effect_name == "crossfade":
                print("crossfade",end=" ")
                if i == 0:
                    clip = CompositeVideoClip([clip.with_effects(vfx.CrossFadeIn(duration=duration))])
                elif i == len(clips) - 1:
                    clip = CompositeVideoClip([clip.with_effects(vfx.CrossFadeOut(duration=duration))])
            elif effect_name == "slide":
                if i == 0:
                    clip = CompositeVideoClip([vfx.SlideIn(duration=duration, side="right").apply(clip)])
                elif i == len(clips) - 1:
                    clip = CompositeVideoClip([vfx.SlideOut(duration=duration, side="left").apply(clip)])
                
            elif effect_name == "rotate":
                if i == 0:
                    clip = vfx.Rotate(lambda t: min(t * 360 / duration, 360)).apply(clip)
                elif i == len(clips) - 1:
                    clip = vfx.Rotate(lambda t: max(360 - (t * 360 / duration), 0)).apply(clip)
                    
            final_clips.append(clip)
        
        return final_clips

    def concatenate_with_effects(self,video_paths, output_path, color_effect = None, effect=None, effect_duration=1.0, music_effect= None, remix = None, subtitle = None):
        """
        Concatenate videos with transition effects
        
        Args:
            video_paths (list): List of paths to input videos
            output_path (str): Path for output video
            effect (str): Type of effect ('fade', 'slide', 'zoom', 'rotate', 'crossfade')
            effect_duration (float): Duration of effect in seconds
        """
        global logo
        try:
            clips = [VideoFileClip(path) for path in video_paths]
            
            if effect:
                clips = self.add_video_effects(clips, effect, effect_duration)
            final_clip = concatenate_videoclips(clips)
            
            # Write output
            if music_effect:
                background_music = AudioFileClip(music_effect).with_volume_scaled(.1).subclipped(0, final_clip.duration)
                audio_loops = []
                while sum(clip.duration for clip in audio_loops) < final_clip.duration:
                    audio_loops.append(background_music)
                background_music = concatenate_audioclips(audio_loops).subclipped(0, final_clip.duration)
                
                original_audio = final_clip.audio
                final_audio = CompositeAudioClip([original_audio, background_music])
            
                final_clip = final_clip.with_audio(final_audio)
            
            if remix:
                remix_vdo = VideoFileClip(remix)

                shortest_duration = min(final_clip.duration, remix_vdo.duration)

                video1_trimmed = final_clip.subclipped(0, shortest_duration)
                
                if color_effect:
                    if color_effect=="B&W":
                        video1_trimmed = vfx.BlackAndWhite().apply(video1_trimmed)
                    else:
                        pass
                    
                video2_trimmed = remix_vdo.with_volume_scaled(0).subclipped(0, shortest_duration)
                
                final_width = 1080
                final_height = 1920

                height_ratio = .6
                actual_video_height = final_height * height_ratio
                bg_video_height = final_height * (1 - height_ratio)
                video1_resized = video1_trimmed.resized(width=final_width, height= actual_video_height ).with_position(("center", "top"))
                video2_resized = video2_trimmed.resized(width=final_width, height= bg_video_height).with_position(("center", "bottom"))

                final_clip = CompositeVideoClip([video1_resized, video2_resized], size=(final_width, final_height))
            
            else:
                final_width = 1080
                final_height = 1920
                actual_video_height = 1920
                video1_resized = final_clip.resized(width=final_width, height= actual_video_height ).with_position(("center", "top"))
                final_clip = CompositeVideoClip([video1_resized], size=(final_width, final_height))
            
            if self.logo:
                _logo = self.logo
                _logo = ImageClip(_logo)

                _logo = _logo.resized(height=self._logo_height)  # Resize the logo to a height of 50 pixels (maintains aspect ratio)

                _logo = _logo.with_opacity(self._logo_opacity).with_position((self._x_pos_logo, self._y_pos_logo)).with_duration(final_clip.duration)

                final_clip = CompositeVideoClip([final_clip, _logo])

            if subtitle:
                print("here")
                final_clip = self.generate_video_with_subtitles(final_clip.copy())
                
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac'
            )
            
            final_clip.close()
            for clip in clips:
                clip.close()
                
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}")
            
            try:
                if 'final_clip' in locals():
                    final_clip.close()
                for clip in clips:
                    clip.close()
            except:
                pass
                
            return False



    def convert_to_mp4(self,mkv_file, output_folder=None):
        """
        Convert MKV file to MP4 format.
        
        Args:
            mkv_file (str or Path): Path to input MKV file
            output_folder (str or Path, optional): Output folder path. If None, 
                creates MP4 in the same folder as input file
        
        Returns:
            tuple: (success: bool, message: str, output_path: Path)
        """
        try:
            # Convert input path to Path object
            input_path = Path(mkv_file)
            
            # Verify input file exists
            if not input_path.exists():
                return False, f"Input file not found: {input_path}", None
                
            # Determine output path
            if output_folder is None:
                # Use same directory as input file
                output_file = input_path.parent / f"{input_path.stem}.mp4"
            else:
                # Use specified output directory
                output_folder = Path(output_folder)
                output_folder.mkdir(parents=True, exist_ok=True)
                output_file = output_folder / f"{input_path.stem}.mp4"
            
            print(f"Converting {input_path.name} to MP4...")
            # Prepare ffmpeg command
            command = [
                'ffmpeg',
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                str(output_file)
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                print("Conversion successful")
                return True,"Conversion successful", result
            else:
                print("Error ::", result.stderr)
                return False, f"FFmpeg error: {result.stderr}", result
                
        except Exception as e:
            print(e)
            return False, f"Error during conversion: {str(e)}", None
        

    def mkv_to_mp4(self,input_path="./Input_video/", output_path=None):
        """
        Convert all MKV files in the input directory to MP4 format.
        
        Args:
            input_path (str): Directory containing MKV files
            output_path (str): Directory for output MP4 files. If None, creates 'converted_videos' in input directory
            time_limit (tuple): Optional (start_seconds, end_seconds) for trimming videos
        
        Returns:
            list: Paths of successfully converted files
        """
        try:
            
            if output_path==None:
                output_path = input_path
            
            input_path = Path(input_path)
            output_path = Path(output_path)

            output_path.mkdir(parents=True, exist_ok=True)
            converted_files = []
            
            mkv_files = list(input_path.glob("*.mkv"))
            
            if not mkv_files:
                print(f"No MKV files found in {input_path}")
                return []
            
            for mkv_file in mkv_files:
                try:
                    output_file = output_path / f"{mkv_file.stem}.mp4"
                    _,_,result = self.convert_to_mp4(mkv_file)
                    if result.returncode != 0:
                        raise Exception(f"FFmpeg error: {result.stderr.decode()}")
                
                    converted_files.append(output_file)
                    print(f"Successfully converted {mkv_file.name}")
                    
                except Exception as e:
                    print(f"Error converting {mkv_file.name}: {str(e)}")
                    continue
            
            return converted_files
        
        except Exception as e:
            print(f"Error in conversion process: {str(e)}")
            return []


    # mkv_to_mp4()
    # convert_to_mp4("./Input_video/recording.mkv","./output/")
    
    def format_timestamp(self,seconds):
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds}"

    def get_text_from_video(self,input_video_path, method="whisper"):
        video = None
        try:
            if not isinstance(input_video_path,VideoFileClip) and not isinstance(input_video_path,CompositeVideoClip):
                if not os.path.exists(input_video_path):
                    raise FileNotFoundError(f"Input video not found: {input_video_path}")
                try:
                    video = mp.VideoFileClip(input_video_path)
                except Exception as e:
                    print(e)
                    raise Exception(f"Failed to load video: {str(e)}")
            else:
                video = input_video_path.copy()
            
            temp_dir = "./temp_audio"
            os.makedirs(temp_dir, exist_ok=True)
            temp_audio_path = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.wav")
            
            try:
                video.audio.write_audiofile(
                    temp_audio_path,
                    logger=None,
                    fps=44100,  
                    nbytes=2,   
                    codec='pcm_s16le'  
                )
                
                if method == 'whisper':
                    if not os.path.exists("./models/"):
                        whisper._download(whisper._MODELS["base"], "./models/", False)
                    model = whisper.load_model("small", download_root="./models/")

                    result = model.transcribe(str(temp_audio_path))

                    segments = []
                    for segment in result["segments"]:
                        segments.append({
                            'text': segment['text'].strip(),
                            'start_time': self.format_timestamp(segment['start']),
                            'end_time': self.format_timestamp(segment['end']),
                            'start_seconds': segment['start'],
                            'end_seconds': segment['end']
                        })
                    
                    return {
                        'full_text': result['text'],
                        'segments': segments
                    }
                    
                else:
                    r = sr.Recognizer()
                    with sr.AudioFile(temp_audio_path) as source:
                        data = r.record(source)
                    text = r.recognize_google(data)
                
                return text
                
            except Exception as e:
                raise Exception(f"Error processing audio: {str(e)}")
                
            finally:
                if video is not None:
                    video.close()
                try:
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary audio file: {str(e)}")
                    
        except Exception as e:
            print(f"Error: {str(e)}")
            return None


    # Main function to add subtitles
    def generate_video_with_subtitles(self,input_video_path, output_video_path = None):
        try:
            subtitle_data = self.get_text_from_video(input_video_path)
            segments = subtitle_data['segments']

            if not isinstance(input_video_path,VideoFileClip) and not isinstance(input_video_path,CompositeVideoClip):
                # Load the video
                video = VideoFileClip(input_video_path)
            else:
                video = input_video_path
            
            print("\n\n",segments,"\n\n")
            base_time = 0
        
            subtitle_clips = []
            for segment in segments:
                start_time = segment['start_seconds']
                end_time = segment['end_seconds']
                text = segment['text']

                text_list = text.split()
                base_time = [(end_time - start_time) / len(text_list)] * len(text_list)
                avg_word_length = sum(len(word) for word in text_list) / len(text_list)
                base_time = [(bt * len(word) / avg_word_length) for word, bt in zip(text_list, base_time)]
                
                while len(text_list) > 0:
                    _base_time = sum(base_time[:self.subtitle_font_window])
                    subtitle = TextClip(
                        font=self.FONT_DIR,
                        text=" ".join(text_list[:self.subtitle_font_window]),
                        stroke_color="black", # Outline color
                        stroke_width=self._sub_stroke_width,
                        font_size=self.subtitle_font_size, color=self._subtitle_color, size=(video.w, None), duration = _base_time, method="caption"
                    ).with_position((self.x_sub_pos, self.y_sub_pos))
                    
                    subtitle.start = start_time
                    subtitle.end = start_time + sum(base_time[:self.subtitle_font_window])
                    start_time = subtitle.end
                    subtitle_clips.append(subtitle)
                    base_time = base_time[self.subtitle_font_window:]
                    text_list = text_list[self.subtitle_font_window:]

            
            final_video = CompositeVideoClip([video] + subtitle_clips)
            if output_video_path:
                final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
            else:
                print("returning video")
                return final_video.copy()
        finally:
            final_video.close()


    def create_framed_video(self,input_video_path, frame_path, output_path=None):
        """
        Creates a video with the input video placed inside a decorative frame.
        
        Args:
            video_path (str): Path to the input video file
            frame_path (str): Path to the frame image (PNG with transparency)
            output_path (str): Path where the output video will be saved
        """
        # Load the video and frame
        
        if not isinstance(input_video_path,VideoFileClip) and not isinstance(input_video_path,CompositeVideoClip):
                # Load the video
            video = VideoFileClip(input_video_path)
        else:
            video = input_video_path
            
        if not isinstance(frame_path,ImageClip):
            frame = ImageClip(frame_path)
        else:
            frame = frame_path
            
    
        frame_width = frame.size[0]
        frame_height = frame.size[1]
        
        inner_width = int(frame_width * 0.99)  # Approximate width of purple area
        inner_height = int(frame_height * 0.99)  # Approximate height of purple area
        
        resized_video = video.resized(width=inner_width, height=inner_height)
        
        
        
        # Create the composite
        final_video = CompositeVideoClip([  # Place video first
            frame.with_duration(video.duration),        # Add frame on top
            resized_video.with_position((160, 5)),
        ], size=frame.size)
        
        
        if output_path:
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        else:
            print("returning video")
            return final_video.copy()
        
        video.close()
        frame.close()
        final_video.close()
    
    # generate_video_with_subtitles("./output_with_logo.mp4", "output_with_subtitles.mp4")

    # v = mp.VideoFileClip("./output_with_logo.mp4")
    # v = generate_video_with_subtitles(v)
    # v.write_videofile("./ab.mp4", codec="libx264", audio_codec="aac")


    def add_logo_to_video(self,input_video_path, logo_path, output_video_path):
        # Load the main video
        video = VideoFileClip(input_video_path)

        # Load the logo image
        logo = ImageClip(logo_path)

        logo = logo.resized(height=self._logo_height)  # Resize the logo to a height of 50 pixels (maintains aspect ratio)

        logo = logo.with_opacity(self._logo_opacity).with_position((self._x_pos_logo, self._y_pos_logo)).with_duration(video.duration)
        # logo = logo.with_opacity(.75).with_position((850, 100)).with_duration(video.duration)

        # Combine the logo with the video
        final_video = CompositeVideoClip([video, logo])

        # Export the final video
        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")




# videos = [
#         r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\output\Sitcoms\seta__0\FINAL.mp4",
#         r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\output\Sitcoms\seta__0\FINAL_.mp4"

# ]

# obj = Editor("JRE")
# obj = Editor("Sitcoms")

# obj.create_framed_video(r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\output\Sitcoms\lota@0_240__2\FINAL.mp4",r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\config\Sitcoms\frame__.png","./framed.mp4")
# obj.trim_video_final(r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\output\JRE\aliens@0_240__0\FINAL.mp4", "00:00:05", "00:01:00", r"./no.mp4")

# obj.concatenate_with_effects(
#     videos,
#     r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\output\Sitcoms\seta__0\_FINAL_.mp4",
#     # effect="fade",
#     effect_duration=.1,
#     # music_effect="Music/inspiring-cinematic-ambient.mp3",
#     # remix="remix/forza_240.mp4",
#     subtitle=True
# )



# import os 
# from google import genai
# from pydantic import BaseModel
# from typing import List
# client = genai.Client(api_key="AIzaSyAIWLIxKL1yCk5Skw1WzNZHvPRyK5jhd6g")

# class subclib(BaseModel):
#     str_content: str
#     start_time: str
#     end_time: str

# class OneYoutubeShortVideo(BaseModel):
#     transcribe: str
#     clips: List[subclib] 


# class MultiYoutubeShorts(BaseModel):
#     clips: List[OneYoutubeShortVideo]
    
# all_segments="""{"text": "Because we still got a national deficit", "start_time": "00:00:0.0", "end_time": "00:00:3.9", "start_seconds": 0.0, "end_seconds": 3.9}\n\n{"text": "that we gotta increase and I gotta line the pockets", "start_time": "00:00:3.9", "end_time": "00:00:6.5200000000000005", "start_seconds": 3.9, "end_seconds": 6.5200000000000005}\n\n{"text": "of all my buddies, you know, Raytheon,", "start_time": "00:00:6.5200000000000005", "end_time": "00:00:8.72", "start_seconds": 6.5200000000000005, "end_seconds": 8.72}\n\n{"text": "Northrop Grumman and Lockheed Martin.", "start_time": "00:00:8.72", "end_time": "00:00:11.16", "start_seconds": 8.72, "end_seconds": 11.16}\n\n{"text": "Like we don\'t want them to get in too far.", "start_time": "00:00:11.16", "end_time": "00:00:13.36", "start_seconds": 11.16, "end_seconds": 13.36}\n\n{"text": "Like don\'t start talking about the reserve", "start_time": "00:00:13.36", "end_time": "00:00:15.8", "start_seconds": 13.36, "end_seconds": 15.8}\n\n{"text": "or don\'t start talking about any of that other stuff.", "start_time": "00:00:15.8", "end_time": "00:00:18.240000000000002", "start_seconds": 15.8, "end_seconds": 18.240000000000002}\n\n{"text": "Like I think that\'s what it is.", "start_time": "00:00:18.240000000000002", "end_time": "00:00:20.0", "start_seconds": 18.240000000000002, "end_seconds": 20.0}\n\n{"text": "Well, I think that\'s also why politicians", "start_time": "00:00:20.0", "end_time": "00:00:22.080000000000002", "start_seconds": 20.0, "end_seconds": 22.080000000000002}\n\n{"text": "or some of them at least are terrified of podcasts.", "start_time": "00:00:22.080000000000002", "end_time": "00:00:25.400000000000002", "start_seconds": 22.080000000000002, "end_seconds": 25.400000000000002}\n\n{"text": "Yeah.", "start_time": "00:00:25.400000000000002", "end_time": "00:00:26.240000000000002", "start_seconds": 25.400000000000002, "end_seconds": 26.240000000000002}\n\n{"text": "Because you do have to talk about them.", "start_time": "00:00:26.240000000000002", "end_time": "00:00:27.8", "start_seconds": 26.240000000000002, "end_seconds": 27.8}\n\n{"text": "But that\'s what makes guys like JD and guys like Trump unique", "start_time": "00:00:27.8", "end_time": "00:00:32.92", "start_seconds": 27.8, "end_seconds": 32.92}\n\n{"text": "in that they will just sit and talk with anybody.", "start_time": "00:00:32.92", "end_time": "00:00:35.64", "start_seconds": 32.92, "end_seconds": 35.64}\n\n{"text": "I mean, he\'s had with Theo Vaughn.", "start_time": "00:00:35.64", "end_time": "00:00:36.92", "start_seconds": 35.64, "end_seconds": 36.92}\n\n{"text": "Theo talked to him about doing Coke.", "start_time": "00:00:36.92", "end_time": "00:00:38.4", "start_seconds": 36.92, "end_seconds": 38.4}\n\n{"text": "That\'s awesome.", "start_time": "00:00:38.4", "end_time": "00:00:39.64", "start_seconds": 38.4, "end_seconds": 39.64}\n\n{"text": "It was so funny.", "start_time": "00:00:39.64", "end_time": "00:00:40.8", "start_seconds": 39.64, "end_seconds": 40.8}\n\n{"text": "Theo\'s amazing.", "start_time": "00:00:40.8", "end_time": "00:00:42.4", "start_seconds": 40.8, "end_seconds": 42.4}\n\n{"text": "It was amazing.", "start_time": "00:00:42.4", "end_time": "00:00:43.24", "start_seconds": 42.4, "end_seconds": 43.24}\n\n{"text": "Theo\'s an ability to be himself no matter who he\'s talking to.", "start_time": "00:00:43.24", "end_time": "00:00:46.32", "start_seconds": 43.24, "end_seconds": 46.32}\n\n{"text": "And him talking to Trump about how he used to love to do Coke.", "start_time": "00:00:46.32", "end_time": "00:00:50.400000000000006", "start_seconds": 46.32, "end_seconds": 50.400000000000006}\n\n{"text": "It was like, and Trump\'s just sitting there,", "start_time": "00:00:50.400000000000006", "end_time": "00:00:52.96", "start_seconds": 50.400000000000006, "end_seconds": 52.96}\n\n{"text": "which was super funny, by the way.", "start_time": "00:00:52.96", "end_time": "00:00:54.68", "start_seconds": 52.96, "end_seconds": 54.68}\n\n{"text": "He\'s sitting like, poor guy.", "start_time": "00:00:54.68", "end_time": "00:00:56.8", "start_seconds": 54.68, "end_seconds": 56.8}\n\n{"text": "Like you see Theo falling apart in front of you.", "start_time": "00:00:56.8", "end_time": "00:00:58.599999999999994", "start_seconds": 56.8, "end_seconds": 58.599999999999994}\n\n{"text": "Like, Jesus Christ, I thought I was running for president here.", "start_time": "00:00:58.599999999999994", "end_time": "00:01:0.759999999999998", "start_seconds": 58.599999999999994, "end_seconds": 60.76}\n\n{"text": "I think I might have helped this young fellow.", "start_time": "00:01:0.759999999999998", "end_time": "00:01:3.9599999999999937", "start_seconds": 60.76, "end_seconds": 63.959999999999994}\n\n{"text": "Who do I need to talk to you about this?", "start_time": "00:01:3.9599999999999937", "end_time": "00:01:5.8799999999999955", "start_seconds": 63.959999999999994, "end_seconds": 65.88}\n\n{"text": "But Kamala didn\'t have the ability to do that.", "start_time": "00:01:5.8799999999999955", "end_time": "00:01:9.200000000000003", "start_seconds": 65.88, "end_seconds": 69.2}\n\n{"text": "Or if she did, nobody brought it out of her.", "start_time": "00:01:9.200000000000003", "end_time": "00:01:10.840000000000003", "start_seconds": 69.2, "end_seconds": 70.84}\n\n{"text": "I was hoping I could.", "start_time": "00:01:10.840000000000003", "end_time": "00:01:12.159999999999997", "start_seconds": 70.84, "end_seconds": 72.16}\n\n{"text": "I really was.", "start_time": "00:01:12.159999999999997", "end_time": "00:01:12.879999999999995", "start_seconds": 72.16, "end_seconds": 72.88}\n\n{"text": "I was hoping I could have a conversation with her.", "start_time": "00:01:12.879999999999995", "end_time": "00:01:14.759999999999991", "start_seconds": 72.88, "end_seconds": 74.75999999999999}\n\n{"text": "There\'s all this talk now that the reason why she didn\'t do it", "start_time": "00:01:14.759999999999991", "end_time": "00:01:17.0", "start_seconds": 74.75999999999999, "end_seconds": 77.0}\n\n{"text": "is because of progressive people in her party, the pushback,", "start_time": "00:01:17.0", "end_time": "00:01:21.120000000000005", "start_seconds": 77.0, "end_seconds": 81.12}\n\n{"text": "which might have some truth to it.", "start_time": "00:01:21.120000000000005", "end_time": "00:01:24.28", "start_seconds": 81.12, "end_seconds": 84.28}\n\n{"text": "But for the record, they offered me two very specific days", "start_time": "00:01:24.28", "end_time": "00:01:29.0", "start_seconds": 84.28, "end_seconds": 89.0}\n\n{"text": "and in different places in the country to travel and then go do it", "start_time": "00:01:29.0", "end_time": "00:01:33.120000000000005", "start_seconds": 89.0, "end_seconds": 93.12}\n\n{"text": "and do it for an hour.", "start_time": "00:01:33.120000000000005", "end_time": "00:01:34.0", "start_seconds": 93.12, "end_seconds": 94.0}\n\n{"text": "And I said I didn\'t want to do that.", "start_time": "00:01:34.0", "end_time": "00:01:35.44", "start_seconds": 94.0, "end_seconds": 95.44}\n\n{"text": "And especially after Trump had done it.", "start_time": "00:01:35.44", "end_time": "00:01:37.400000000000006", "start_seconds": 95.44, "end_seconds": 97.4}\n\n{"text": "Here in three hours, I\'m like, this is the only way to do it.", "start_time": "00:01:37.400000000000006", "end_time": "00:01:40.31999999999999", "start_seconds": 97.4, "end_seconds": 100.32}'"""
# response = client.models.generate_content(
#         model = 'gemini-2.0-flash-lite-preview-02-05',
#         # model = 'gemini-2.0-flash-001',
#         contents = f"""please generate 50 to 58 seconds Youtube shorts video or list of 50 to 58 seconds shorts videos only in case when video contain multiple interesting topics , from provided video content where each video duration should be between 50 seconds to 58 seconds only, for one video try to make as less cuts as possible while making sure not including unecessary parts and also that short video should be interesting and every subclib should be in continuation of same strictly topic avoid abrupt transitions and fragmented storytelling. \n\n Remember each video duration strictly should be between between 55 seconds to 58 seconds, Here is the video clip content : `{all_segments}`")""",
#         config = {
#             'response_mime_type' : 'application/json',
#             'response_schema' : list[OneYoutubeShortVideo]
#         }
#     )

# clips:List[OneYoutubeShortVideo] = response.parsed
# print(clips)

