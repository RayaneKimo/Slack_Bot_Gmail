import base64
from googleapiclient.discovery import build

def get_full_email_content(creds):
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
    else:
        print("Messages:")
        for message in messages:
            
            msg = service.users().messages().get(userId='me', id=message["id"], format='full').execute()
            # msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            payload = msg['payload']
            headers = payload['headers']
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            print(f"Subject: {subject}")

            # Get the body of the email
            if 'parts' in payload:
                for part in payload['parts']:
                   if  part['mimeType'] == 'text/html':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        return body, payload
            else:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                return body, payload