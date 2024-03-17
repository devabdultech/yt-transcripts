import whisper
import os
import scrapetube
from pytube import YouTube
import subprocess
import json
import re
from pytube.exceptions import AgeRestrictedError
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

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
        print(Fore.GREEN + "Successfully Converted :)")
        # Remove the MP4 file after successful conversion
        os.remove(input_file)
        print(Fore.YELLOW + "Removed the original MP4 file.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + "Conversion failed :(")

# Define the list of channels to scrape
channels_to_scrape = [
    # "SenaVL",
    "nbrainyvalo",
    "CoachKonpeki",
    "wasabi_plays",
    "skillcappedvalorant"
]

for channel_name in channels_to_scrape:
    # Create a folder for the channel
    channel_folder = create_channel_folder(channel_name)
    
    # Load existing video titles from JSON file
    existing_videos = set()
    json_filename = os.path.join(channel_folder, f"{channel_name}_video_details.json")
    if os.path.exists(json_filename):
        with open(json_filename, "r") as json_file:
            existing_data = json.load(json_file)
            for video_info in existing_data:
                existing_videos.add(video_info["video_title"])

    # Get all video IDs from the channel
    videos = scrapetube.get_channel(channel_username=channel_name)

    # Initialize an empty list to store video details
    video_details = []

    # Initialize a list to store IDs of age-restricted videos
    age_restricted_videos = []

    # Iterate through each video ID
    for video in videos:
        video_id = video['videoId']
        try:
            yt = YouTube(f'http://youtube.com/watch?v={video_id}')
            title = clean_filename(yt.title)

            # Check if video title already exists
            if title in existing_videos:
                print(Fore.YELLOW + f"Skipping {title}. Already processed.")
                continue
            
            filename = title + ".mp4"
            audio = yt.streams.filter(only_audio=True).first()

            # Download the audio
            print(Fore.CYAN + f"Downloading audio for {title}")
            audio.download(max_retries=5, output_path=channel_folder, filename=filename)

            # Convert MP4 to MP3
            mp4_file_name_cleaned = title + ".mp4"
            mp4_file_path = os.path.join(channel_folder, mp4_file_name_cleaned)
            mp3_file_name_cleaned = title + ".mp3"
            mp3_file_path = os.path.join(channel_folder, mp3_file_name_cleaned)
            convert_mp4_to_mp3(mp4_file_path, mp3_file_path)

            # Transcribe the audio
            model = whisper.load_model("base")
            print(Fore.CYAN + f"Transcribing audio for {title}")
            try:
                result = model.transcribe(mp3_file_path)
                transcription_text = result["text"]
                print(Fore.GREEN + "Transcription successful.")
            except Exception as e:
                print(Fore.RED + f"Transcription failed for {title}: {str(e)}")
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

            # Delete the MP3 audio file
            os.remove(mp3_file_path)
            print(Fore.LIGHTYELLOW_EX + "Transcription Done. Removed audio file")

        except AgeRestrictedError:
            print(Fore.YELLOW + f"Video {video_id} is age-restricted. Skipping...")
            # Add the ID of the age-restricted video to the list
            age_restricted_videos.append(video_id)
            continue

        # Write the list of video details to a JSON file after processing each video
        with open(json_filename, "w") as json_file:
            json.dump(video_details, json_file, indent=4)

    # Save the IDs of age-restricted videos to a JSON file
    age_restricted_json_filename = os.path.join(channel_folder, f"{channel_name}_age_restricted_videos.json")
    with open(age_restricted_json_filename, "w") as json_file:
        json.dump(age_restricted_videos, json_file, indent=4)
