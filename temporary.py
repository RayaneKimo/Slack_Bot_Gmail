import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import google.generativeai as genai
from dotenv import load_dotenv
import google.generativeai as genai
import pathlib
from dotenv import load_dotenv
import os.path
from slack_sdk import WebClient
from utils.AuthGmail import authenticate_gmail
from utils.GetContent import get_full_email_content
from utils.HeadLessScreenShot import take_screen_shot
from utils.GetUserAudio import download_vocal
from slack_sdk import WebClient

# Initialize a Gemini model appropriate for your use case.
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


prompt = """Please hear the audio, and answer it without repeating the question."""



@app.event("message")
def handle_message_events(body, say):


    # converter = html2text.HTML2Text()
    # converter.ignore_links = False  # Preserve links
    # slack_message = converter.handle(email_body)
    event = body.get("event", {})
    thread_ts = event.get("thread_ts")  # Check if the message is in a thread
    channel_id = event.get("channel")

    # Check if the message is in a thread (means a reply)
    if thread_ts : 
        user_reply = event.get("text")
        print(f"User replied in thread: {user_reply}")
        # Optionally, acknowledge the reply in Slack
        say(
            text=f"Your reply has been processed: {user_reply}",
            thread_ts=thread_ts,  # Reply in the same thread
            channel=channel_id
        )
            
    else : 
            creds = authenticate_gmail()
            email_body, payload = get_full_email_content(creds)
            take_screen_shot(email_body)
            client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))    
            # response = client.files_upload_v2(
            response = client.files_upload_v2(
                channels=channel_id,  # Replace with your channel ID
                file= "screenshot.png",  # Path to the screenshot
                title="New Email",
                initial_comment="Here's a new email:",
            )
    

@app.action("reply_to_email")
def handle_button_click(ack, body, client):
    # Acknowledge the action
    ack()

    # Get the trigger ID from the payload
    trigger_id = body["trigger_id"]

    # Open a modal for the user to reply
    try:
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "reply_modal",
                "title": {
                    "type": "plain_text",
                    "text": "Reply to Email"
                },
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "reply_message",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "reply_input",
                            "multiline": True
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "Your Reply"
                        }
                    }
                ],
                "submit": {
                    "type": "plain_text",
                    "text": "Send"
                }
            }
        )
    except Exception as e:
        print(f"Error opening modal: {e}")

# Listen to a vocal message and generate a response
# @app.event("message")
# def handle_message_events(body, say):
#     download_vocal(body)
#     response = model.generate_content([
#                 prompt,
#                 {
#                     "mime_type": "audio/wav",
#                     "data": pathlib.Path('audio_message.wav').read_bytes()
#                 }
#             ])
#     say(f"{response.text}")




# Start your app
if __name__ == "__main__":
    
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()