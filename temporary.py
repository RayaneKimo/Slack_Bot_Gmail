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
from utils.GetContent import fetch_inbox_emails, decode_content
from utils.HeadLessScreenShot import take_screen_shot
from utils.GetUserAudio import download_vocal
from slack_sdk import WebClient
from googleapiclient.discovery import build 
import base64
import html2text
from slack_sdk.errors import SlackApiError


# Initialize a Gemini model appropriate for your use case.
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
prompt = """Please hear the audio, and answer it without repeating the question."""
messages = []

creds = authenticate_gmail()
service = build('gmail', 'v1', credentials=creds)
messages = fetch_inbox_emails(service, labelIds=['INBOX'])
messages = [{**msg, "content": decode_content(service, msg)[2]} for msg in messages]
unread_messages = fetch_inbox_emails(service, labelIds=['INBOX', 'UNREAD'])



def Aggregate_messages(messages):
    """Aggregate the messages in the inbox"""
    context= ""
    for i, msg in enumerate(messages): 
         context =  context + f"\n Message {i} : \n " + base64.urlsafe_b64decode(msg["content"]).decode('utf-8') + " \n"
    converter = html2text.HTML2Text()
    converter.ignore_links = False  # Preserve links
    context = converter.handle(context)
    return context

def Analyze_client_request(client_message, context, client_audio): 
    prompt = f"""You are an AI assistant. Gather all the inputs (audio, text, and image) you are afforded and analyze:\n
         - First, if the client wants to reply to the email and he has provided a reply in the thread, then formulate a professional
         email response according to its audio and text inputs (**Without mentioning the Subject in the response**).\n
          You should respond with a formal email response :  Entrance + Body + Conclusion + Signature\n

         - Second, if the client request is not a reply to an email or it's misunderstood, then reply with a message accordingly, either
         'Sorry I didn't get your request. Could you please provide more detail?'\n
         
         Here is the context of the email conversation: \n{context} \n
         
         """
    
    if client_message and client_audio:
            response = model.generate_content([
                prompt, 
                client_message,
                {
                    "mime_type": "audio/wav",
                    "data": pathlib.Path(client_audio).read_bytes()
                }
            ])
            return response.text
    elif client_message and not client_audio:
            
            response = model.generate_content([
                prompt,
                client_message
            ])
            return response.text
    elif not client_message and client_audio:
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "audio/wav",
                    "data": pathlib.Path(client_audio).read_bytes()
                }
            ])
            return response.text


@app.event("message")
def handle_message_events(body, say):


    event = body.get("event", {})
    thread_ts = event.get("thread_ts")  # Check if the message is in a thread
    channel_id = event.get("channel")
 
    # Check if the message is in a thread (means a reply)
    if thread_ts : 
        client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        uploaded_chat = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,  # Timestamp of the parent message
            inclusive=True  # Include the parent message in the response
        )
        # Get mail context 
        first_msg_ID = uploaded_chat["messages"][0]["files"][0]["name"]
        first_msg = [message for message in messages if message["id"] == first_msg_ID][0]
        discussion = [message for message in messages if message["threadId"] == first_msg["threadId"]]
        context = Aggregate_messages(discussion)

        
        if event.get("files") :
            if  event.get("files")[0]["filetype"] == "m4a" and  event.get("text"):
                download_vocal(body)
                user_reply = event.get("text")
                response = Analyze_client_request(user_reply, context, 'audio_message.wav')

            elif event.get("files")[0]["filetype"] == "m4a" and not event.get("text"):
                download_vocal(body)
                response = Analyze_client_request(None, context, 'audio_message.wav')
        
        else :
             if event.get("text"):
                user_reply = event.get("text")
                response = Analyze_client_request(user_reply, context, None)
             else : 
                response = "Sorry I didn't get your request. Could you please provide more detail?"
        
        
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,  # Reply in the same thread
            text=response,  # Fallback text
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Send Email"
                            },
                            "style": "primary",  # Green button
                            "action_id": "send_email_button"  # Unique ID for the button action
                        }
                    ]
                }
            ]
            )
        
    else : 
             
            
            event = body.get("event", {})
            channel_id = event.get("channel")
            message = messages[0]
            email_body, payload, hashed_text =  decode_content(service, message)
            take_screen_shot(email_body)
            client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))    
            # response = client.files_upload_v2(

            response = client.files_upload_v2(
                channels=channel_id,  # Replace with your channel ID
                file= "screenshot.png",  # Path to the screenshot
                title="New Email",
                initial_comment="Here's a new email:",
                filename=str(message["id"])
               
            )
            # file_id = response["file"]["name"]
            # file_info = client.files_info(file=file_id)
            # meta = file_info["file"]["metadata"]

            print()
   

@app.action("send_email_button")
def handle_button_click(ack, body, client):
    # Acknowledge the button click
    ack()

    # Get the trigger ID (required to open a dialog or modal)
    trigger_id = body["trigger_id"]

    # Open a confirmation dialog
    try:
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "callback_id": "confirm_send_email",
                "title": {
                    "type": "plain_text",
                    "text": "Confirm Email"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Are you sure you want to send this email?"
                        }
                    }
                ],
                "submit": {
                    "type": "plain_text",
                    "text": "Send"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                }
            }
        )
    except SlackApiError as e:
        print(f"Error opening confirmation dialog: {e.response['error']}")

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