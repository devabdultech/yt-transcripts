import whisper
import os
import scrapetube
from pytube import YouTube
import subprocess
import json
import re

# Define a function to create a folder for the channel if it doesn't exist


def create_channel_folder(channel_name):
    folder_path = f"./{channel_name}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

# Function to clean the filename from invalid characters


def clean_filename(filename):
    return re.sub(r'[^\w\s.-]', '', filename)

# Convert mp4 to mp3


def convert_mp4_to_mp3(input_file, output_file):
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_file,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "192k",
        "-ar", "44100",
        "-y",
        output_file
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Successfully Converted :)")
        # Remove the MP4 file after successful conversion
        os.remove(input_file)
        print("Removed the original MP4 file.")
    except subprocess.CalledProcessError as e:
        print("Conversion failed :(")


# Define the list of channels to scrape
channels_to_scrape = [
    # "eSportsAndy",
    # "theguide_val",
    # "SenaVL",
    # "DreamWellYT",
    # "wasabi_plays",
    # "skillcappedvalorant",
    # "ddoshii",
    "platoonval",
    # "FocusFPS",
    # "nbrainyvalo",
    # "rooneyFPS",
    # "SeroGuides",
    # "WestProter",
    # "rbguidesval",
    # "sondo301_"
]

for channel_name in channels_to_scrape:
    # Initialize an empty list to store video details
    video_details = []

    # Get all video IDs from the channel
    videos = scrapetube.get_channel(channel_username=channel_name)

    # Create a folder for the channel
    channel_folder = create_channel_folder(channel_name)

    # Iterate through each video ID
    for video in videos:
        video_id = video['videoId']
        yt = YouTube(f'http://youtube.com/watch?v={video_id}')
        title = clean_filename(yt.title)
        filename = title + ".mp4"
        audio = yt.streams.filter(only_audio=True).first()

        # Download the audio
        print(f"Downloading audio for {title}")
        audio.download(
            max_retries=3, output_path=channel_folder, filename=filename)

        # Convert MP4 to MP3
        mp4_file_name_cleaned = title + ".mp4"
        mp4_file_path = os.path.join(channel_folder, mp4_file_name_cleaned)
        mp3_file_name_cleaned = title + ".mp3"
        mp3_file_path = os.path.join(channel_folder, mp3_file_name_cleaned)
        convert_mp4_to_mp3(mp4_file_path, mp3_file_path)

        # Transcribe the audio
        model = whisper.load_model("base")
        print(f"Transcribing audio for {title}")
        try:
            result = model.transcribe(mp3_file_path)
            transcription_text = result["text"]
            print("Transcription successful.")
        except Exception as e:
            print(f"Transcription failed for {title}: {str(e)}")
            transcription_text = ""

        # Create a JSON object containing video details
        video_info = {
            "channel_name": channel_name,
            "channel_url": f"https://www.youtube.com/@{channel_name}/videos",
            "video_title": title,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "transcription": transcription_text
        }

        # Add the video info to the list
        video_details.append(video_info)

        # Write the list of video details to a JSON file
        json_filename = os.path.join(
            channel_folder, f"{channel_name}_video_details.json")
        with open(json_filename, "w") as json_file:
            json.dump(video_details, json_file, indent=4)
