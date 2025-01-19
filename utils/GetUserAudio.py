from moviepy import *
import requests
import os

def download_vocal(body) : 
    """Download the vocal message from the event body
    
    Keyword arguments:
    body -- body of the event
    
    """
    

    url = body['event']['files'][0]['aac']

    # Set the headers with the OAuth token
    headers = {
        "Authorization": f"Bearer {os.environ.get('SLACK_BOT_TOKEN')}"
    }
    # Send a GET request to download the file
    response = requests.get(url, headers=headers)
    bytes_data = response.content

    # Check if the request was successful
    if response.status_code == 200:
        # Save the file to disk
        with open("audio_message.mp4", "wb") as f:
            f.write(bytes_data)
        audio = AudioFileClip("audio_message.mp4")
        audio.write_audiofile("audio_message.wav")
        print("File downloaded successfully!")
        # os.remove("audio_message.mp4")

    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
        print(f"Response: {response.text}")