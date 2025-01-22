import base64


def fetch_inbox_emails(service, labelIds=['INBOX']):
    """Fetches the emails from the inbox.
    Args:
        service: Authorized Gmail API service instance.
        labelIds: The labelIds of the messages to retrieve.
    """
    
    results = service.users().messages().list(userId='me', labelIds=labelIds).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
    else:
        print("Messages loaded successfully.")
    return  messages


def decode_content(service, message):
            
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
                        return body, msg, part['body']['data']
            else:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                return body, msg, part['body']['data']