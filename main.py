import openai
import re
import requests
import json
import os
import streamlit as st
from PIL import Image
from multiprocessing import Process
import pyttsx3


def delete_folder_content(folder_path):
    # check if the folder exists
    if os.path.exists(folder_path):
        # get a list of all the files and folders in the given folder
        files = os.listdir(folder_path)
        # iterate through the list and delete each file and folder
        for file in files:
            file_path = os.path.join(folder_path, file)
            # check if the file is a directory
            if os.path.isdir(file_path):
                # if it is a directory, recursively call the function to delete its content
                delete_folder_content(file_path)
            else:
                # if it is a file, delete it
                os.unlink(file_path)
        
    else:
        print(f"{folder_path} does not exist.")

# Initialize the TTS engine
engine = pyttsx3.init()

# Set the voice to male
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)


# Set the speed of the voice
engine.setProperty('rate', 150)


st.set_page_config(page_title="Video Downloader", page_icon=":movie_camera:", layout="wide")


def download_video(url, i, j, keywords):
    video_data = requests.get(url).content
    with open(f"videos/paragraph{i}_{j}.mp4", "wb") as f:
        f.write(video_data)
    st.success(f"Downloaded video {j+1} for paragraph {i} for the keywords : {keywords}")

# list to store the keywords
video_keywords = []


# create the folder if it doesnt exist
if not os.path.exists("videos"):
    os.makedirs("videos")

api_key = "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"
openai.api_key = api_key

# Drag and drop the article text file
article_file = st.file_uploader("Drag and drop the article text file here or click to browse", type=["txt"])
# Get desired video resolution from the user
previous_width, previous_height = st.number_input("Enter the desired video width:", value=1280), st.number_input("Enter the desired video height:", value=720)

if article_file is not None:
    # Read the contents of the article text file
    with open(article_file.name, "r") as f:
        article = f.read()

    # Write the article text and create an empty span element
    st.write(article)
    word_span = st.empty()


    delete_folder_content('videos')
    # check if the file exists
    if os.path.exists("audio.mp3"):
        # remove the file
        os.remove("audio.mp3")
        print(f"audio.mp3 removed successfully.")
    else:
        print(f"audio.mp3 does not exist.")

    # saving the artice as voice clip file
    engine.save_to_file(article, "audio.mp3")
    engine.runAndWait()

    st.success("Audio file created and played")


    # Split the article into paragraphs
    paragraphs = re.split(r'\n\n', article)

    # Initialize a list to store the keywords
    keywords = []

    
    # Extract keywords from each paragraph
    for i, paragraph in enumerate(paragraphs):
        # Use the API to extract the best keywords from the paragraph for video search
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"extract the best 1 plaikeyword from this paragraph that can be used to search for related videos to the paragraph content: {paragraph}",
            max_tokens=50,
            temperature=0.5,
        )
        keywords_str = response["choices"][0]["text"].strip()
        keywords_list = keywords_str.split(",")
        print(keywords_list)

        # Search for videos related to the keywords
        url = f"https://api.pexels.com/videos/search?query={keywords_list}&per_page=15"
        headers = {
            "Authorization": "MFLaI1gk5cym0f6kEXNESjYbzVSopCKBHHoAicdxpgUVgP79CSvSCD9B"
        }
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            st.error(f"Error searching for videos for paragraph {i}")
            continue
        else:
            try:
                video_urls = json.loads(r.text)["videos"]
            except:
                st.error(f"Error searching for videos for paragraph {i}")
                continue

        processes = []
        for j, video in enumerate(video_urls):
            video_url = video["video_files"][0]["link"]
            width = video["video_files"][0]["width"]
            height = video["video_files"][0]["height"]

            if width == previous_width and height == previous_height:
                # Download the video and save it with the paragraph number
                download_video(video_url, i, j, keywords_list)
                
                video_keywords.append(keywords_list)
            else:
                pass
                #st.warning(f"Video width and height not the same as desired resolution. Video not downloaded.")
        for process in processes:
            process.join()
    
    st.write("Keywords: " + ",".join(keywords_list))
    st.info("Videos downloaded and saved to the 'videos' folder")
    # Display the downloaded videos in a 5xn grid layout
    st.header("Downloaded Videos")
    video_files = [f for f in os.listdir("videos") if f.endswith(".mp4")]
    while not video_files:
        video_files = [f for f in os.listdir("videos") if f.endswith(".mp4")]
    col1, col2, col3, col4 = st.columns(4)
    for i in range(0,len(video_files), 4):

        try:
            video1 = video_files[i]
            col1.video(open(f"videos/{video1}", "rb").read())
        except:
            pass
        try:
            video2 = video_files[i+1]
            col2.video(open(f"videos/{video2}", "rb").read())  
        except:
            pass
        try:
            video3 = video_files[i+2]
            col3.video(open(f"videos/{video3}", "rb").read()) 
        except:
            pass
        try:
            video4 = video_files[i+3]
            col4.video(open(f"videos/{video4}", "rb").read())
        except:
            pass
         
    

    st.info("Editing Final video...")
    
    import moviepy.editor as mp

    # Assemble all the downloaded videos into one
    video_clips  = [mp.VideoFileClip('videos/'+f) for f in os.listdir("videos") if f.endswith(".mp4")]
    final_video = mp.concatenate_videoclips(video_clips, method="compose")

    
    # Add the audio clip
    audio_clip = mp.AudioFileClip("audio.mp3")
    final_video = final_video.set_audio(audio_clip)

    
    # Save the final video
    final_video.write_videofile("final_video.mp4")
    
    progress_bar = st.progress(0)
    for i, frame in enumerate(final_video.iter_frames()):
        progress_bar.progress(i / final_video.fps / final_video.duration)
    
    st.success("Final video created")

    

    # Dispalay Final video
    st.header("Final Video : ")
    st.video(open("final_video.mp4", "rb").read())