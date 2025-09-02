from trim import Editor
import json
import ast
import os
import random
import configparser
from typing import List
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState
from langgraph.graph import END
from typing import List,Literal
from langgraph.graph import StateGraph, START
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, RemoveMessage, AIMessage



import os 
from google import genai
from pydantic import BaseModel
from typing import List


client = genai.Client(api_key="AIzaSyAIWLIxKL1yCk5Skw1WzNZHvPRyK5jhd6g")


def get_graph(config,account):
    try:
        APIKey = config.get("AzureCredentials","APIKey").strip()
        Endpoint = config.get("AzureCredentials","Endpoint").strip()
        Deployment = config.get("AzureCredentials","Deployment").strip()
        version = config.get("AzureCredentials","version").strip()
        
        _remix_dir = config.get("remixdirectory","_dir").strip()
        remix_video_value = config.get("remixdirectory","type").strip()
        remix_video_value = None if remix_video_value=="None" else remix_video_value

        os.environ['GOOGLE_CSE_ID'] = config.get("GoogleCred","GOOGLE_CSE_ID").strip()
        os.environ['GOOGLE_API_KEY'] = config.get("GoogleCred","GOOGLE_API_KEY").strip()
        
        
        account_prompt = config.get("Prompt","prompt").strip()

        
        _Editor_obj = Editor(account)
    except Exception as e:
        print("Error Occured while reading config: ",e)
        
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite-preview-02-05")

    if remix_video_value == "random":
        remix_video_value = os.path.join(_remix_dir,random.choice(os.listdir(_remix_dir))) 
    elif remix_video_value is not None:
        remix_video_value = os.path.join(_remix_dir,remix_video_value) 


    from langchain_openai import AzureChatOpenAI
    llm = AzureChatOpenAI(temperature = 0.2,
                                    deployment_name=Deployment,
                                    openai_api_version=version,
                                    openai_api_key=APIKey, 
                                    azure_endpoint=Endpoint)


    class subclib(BaseModel):
        str_content: str
        start_time: str
        end_time: str

    class OneYoutubeShortVideo(BaseModel):
        yt_title: str
        transcribe: str
        clips: List[subclib] 


    class MultiYoutubeShorts(BaseModel):
        clips: List[OneYoutubeShortVideo]
        

    class State(MessagesState):
        input_video_path: str
        transcribtion: str
        all_segments: str
        clips : List[OneYoutubeShortVideo]
        output_video_path: str
        music_effect: str
        remix: str

    def transcriber(state:State) -> Literal["clipgeneration"]:
        try:
            print("\n\n----------- transcriber ---------\n\n")
            _video_path =  state.get("input_video_path",None)
            if _video_path and os.path.exists(_video_path):
                try:
                    transcribtion_details = _Editor_obj.get_text_from_video(_video_path)
                    transcribtion = transcribtion_details["full_text"]
                    all_segments = [json.dumps(clip) for clip in transcribtion_details["segments"]]
                    return {"messages":HumanMessage(content=transcribtion), "all_segments":HumanMessage(content="\n\n".join(all_segments))}
                except Exception as e:
                    print(e)
                    return END
            return END
        except Exception as e:
            print(e)
            return e
        

        
    def ClipGeneration(state:State) -> Literal["FinalVideoEditor"]:
        try:
            print("\n\n----------- Clip generation ---------\n\n")
            all_segments = state.get("all_segments").content
            # editorllm = llm.with_structured_output(MultiYoutubeShorts)
            # prompt = [SystemMessage(content="You are an Advance video editor for Youtube Shorts who provides the best 50-58 seconds video clips duration based on the content so it can be combinded to make a good youtube video shorts.Try to include the interesting and funny parts from video.each video duration should be between 50 seconds to 58 seconds only.")] 
            # prompt += [HumanMessage(f"please generate 50 to 58 seconds Youtube shorts video or list of 50 to 58 seconds shorts videos only in case when video contain multiple interesting topics , from provided video content where each video duration should be between 50 seconds to 58 seconds only, \
            #     for one video try to make as less cuts as possible while making sure not including unecessary parts and also that short video should be interesting and every subclib should be in continuation of same strictly topic avoid abrupt transitions and fragmented storytelling. \n\n Remember each video duration strictly should be between between 55 seconds to 58 seconds, Here is the video clip content : `{all_segments}`")]

            # clips = editorllm.invoke(prompt)
            # print(clips)
            # return {"clips" : clips.clips}
            
            print(all_segments)
            response = client.models.generate_content(
                model = 'gemini-2.0-flash-001',
                # model = 'gemini-2.0-flash-lite-preview-02-05',
                contents = account_prompt + f"""
                Generate Youtube shorts video or list of shorts videos from given transcription, multiple videos should be created only in case when video contain multiple interesting topics , 
                from provided video transcription, where each video duration should be between 50 seconds seconds only, 
                for OneYoutubeShortVideo video try to make as less cuts as possible while making sure short video should be interesting and every subclib should be in continuation of same topic,
                avoid abrupt transitions and fragmented storytelling.
                Remember each video duration strictly should be of 1 minute seconds, 
                Here is the video transcription content  : `{all_segments}`").
                Strictly Make sure each OneYoutubeShortVideo short should be of 50 seconds .
                """,
                config = {
                    'response_mime_type' : 'application/json',
                    'response_schema' : list[OneYoutubeShortVideo]
                }
            )
            clips:List[OneYoutubeShortVideo] = response.parsed
            
            print(clips)
            return {"clips" : clips}
        except Exception as e:
            print(e)
            return e
        
    def concatVideos(state:State) -> Literal["__end__"]:
        try:
            print("\n\n----------- FinalVideoEditor ---------\n\n")
            
            music_effect = state.get("music_effect")
            remix = state.get("remix")
            
            print(f""" total videos generated {len(state.get("clips"))}""")
            for idx, allclips in enumerate(state.get("clips")):
            
                output_dir_path = state.get("output_video_path")
                input_video_path = state.get("input_video_path")
                video_clipped_path = os.path.join(output_dir_path ,input_video_path.split("/")[-1].split("\\")[-1].split(".")[0] + f"__{idx}")
                
                os.makedirs(video_clipped_path, exist_ok=True)

                for id,clip in enumerate(allclips.clips):
                    _Editor_obj.trim_video_final(input_video_path,clip.start_time.split(".")[0],clip.end_time.split(".")[0],os.path.join(video_clipped_path,str(id)+".mp4"))

                videos = [os.path.abspath(os.path.join(video_clipped_path,p)) for p in os.listdir(video_clipped_path)]
                print(videos)
                json_dump = {'title': allclips.yt_title}
                with open(f"{video_clipped_path}/title.json", "w") as f:
                    json.dump(json_dump, f)
                    
                flag = _Editor_obj.concatenate_with_effects(
                    video_paths=videos,
                    output_path=f"{video_clipped_path}/FINAL.mp4",
                    # effect="fade",
                    effect_duration=0.1,
                    music_effect=music_effect,
                    remix=remix,
                    subtitle=True
                )
            return {"messages": "video editing successful" if  flag else "not able to edit video "}
        except Exception as e:
            print(e)
        
        
    workflow = StateGraph(State)
    workflow.add_node("transcriber", transcriber)
    workflow.add_node("clipgeneration", ClipGeneration)
    workflow.add_node("FinalVideoEditor", concatVideos)
    workflow.add_edge("transcriber", "clipgeneration")
    workflow.add_edge("clipgeneration", "FinalVideoEditor")
    workflow.add_edge("FinalVideoEditor", END)
    workflow.add_edge(START, "transcriber")

    graph = workflow.compile()
    
    return graph

# display(Image(graph.get_graph().draw_mermaid_png()))

# x = graph.invoke(
#     {
#         "input_video_path":r"C:\Users\SIVERMA\Documents\Experimenting\Youtube\input\videoplayback_7.mp4",
#         "output_video_path":"./output",
#         "remix":remix_video_value
#     }
# )


    