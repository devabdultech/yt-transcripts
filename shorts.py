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
    "rooneyFPS",
    "SenaVL",
    "SeroGuides",
    "sondo301_",
    "theguide_val",
    "WestProter",
    "CoachKonpeki"
]

for channel_name in channels_to_scrape:
    # Create a folder for the channel
    channel_folder = create_channel_folder(channel_name)
    
    # Load existing short titles from JSON file
    existing_shorts = set()
    json_filename = os.path.join(channel_folder, f"{channel_name}_short_details.json")
    if os.path.exists(json_filename):
        with open(json_filename, "r") as json_file:
            existing_data = json.load(json_file)
            for short_info in existing_data:
                existing_shorts.add(short_info["short_title"])

    # Get all short IDs from the channel
    shorts = scrapetube.get_channel(channel_username=channel_name, content_type='shorts')

    # Initialize an empty list to store short details
    short_details = []

    # Initialize a list to store IDs of age-restricted shorts
    age_restricted_shorts = []

    # Iterate through each short ID
    for short in shorts:
        short_id = short['videoId']
        try:
            yt = YouTube(f'http://youtube.com/shorts/{short_id}')
            title = clean_filename(yt.title)

            # Check if short title already exists
            if title in existing_shorts:
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

            # Create a JSON object containing short details
            short_info = {
                "channel_name": channel_name,
                "channel_url": f"https://www.youtube.com/@{channel_name}/shorts",
                "short_title": title,
                "short_url": f"https://www.youtube.com/watch?v={short_id}",
                "transcription": transcription_text
            }

            # Add the short info to the list
            short_details.append(short_info)

            # Delete the MP3 audio file
            os.remove(mp3_file_path)
            print(Fore.LIGHTYELLOW_EX + "Transcription Done. Removed audio file")

        except AgeRestrictedError:
            print(Fore.YELLOW + f"short {short_id} is age-restricted. Skipping...")
            # Add the ID of the age-restricted short to the list
            age_restricted_shorts.append(short_id)
            continue

        # Write the list of short details to a JSON file after processing each short
        with open(json_filename, "w") as json_file:
            json.dump(short_details, json_file, indent=4)

    # Save the IDs of age-restricted shorts to a JSON file
    age_restricted_json_filename = os.path.join(channel_folder, f"{channel_name}_age_restricted_shorts.json")
    with open(age_restricted_json_filename, "w") as json_file:
        json.dump(age_restricted_shorts, json_file, indent=4)
