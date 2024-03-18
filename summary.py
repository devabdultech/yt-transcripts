import os
import json
import anthropic
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Initialize Anthropoc client
client = anthropic.Anthropic(api_key="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")

# Define a function to process transcriptions
def process_transcriptions(folder_path):
    # Iterate over JSON files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith("_video_details.json"):
            json_file_path = os.path.join(folder_path, filename)
            print(Fore.BLUE + f"Processing file: {json_file_path}")
            # Load JSON data from the file
            with open(json_file_path, "r") as json_file:
                video_details = json.load(json_file)
            # Iterate over each video object
            for video_info in video_details:
                # Check if "transcriptions" key exists
                if "transcription" in video_info:
                    transcription = video_info["transcription"]
                    # Define the prompt
                    print(Fore.CYAN + "Sending transcription to Anthropoc API for summarization...")
                    # Call the Anthropoc API to generate summary
                    message = client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=2048,
                        temperature=0.0,
                        system="Here is a transcript from a video made by a Valorant Guide YouTuber. Take all of the information from this transcript of their video, and turn them into a well-organized, informative article. Make sure to give titles to strategies, and not to repeat information needlessly. Each strategy should be detailed enough to include the nuances in what the YouTuber is saying, so make sure to capture all of the details from their advice while keeping your sentences clear and concise.",
                        messages=[
                            {"role": "user", "content": transcription}
                        ]
                    )
                    print(Fore.GREEN + "Summary generated successfully!")
                    # Update the object with the summary response
                    video_info["summary"] = message.content[0].text

            # Save the updated JSON data back to the file
            with open(json_file_path, "w") as json_file:
                json.dump(video_details, json_file, indent=4)
            print(Fore.YELLOW + "Updated JSON file saved.")

# Define the folder path containing JSON files
folder_path = "./WestProter"

# Process transcriptions for each JSON file in the folder
process_transcriptions(folder_path)
