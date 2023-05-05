import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import messaging
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# Replace with the path to your Firebase service account JSON file
SERVICE_ACCOUNT_FILE = '/home/ryanbert/Documents/firebase.json'

# Set up Firebase Admin SDK with the provided service account
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
firebase_admin.initialize_app(cred)

# Set up Firestore client
db = firestore.client()

# Set the target FCM token
target_token = 'fOFHsByJT46FP2jB2yMUyC:APA91bG2v0yyyq12XiTm8CDQJuljg7s5TTZXHDTEMgcgGPM-2E58VPe-ITOrK1488JRwwdrUQxEDL3jNkzQ_O4AiH6uujNONDyo38THqfCd8-g5L6aU8CMuJtm6032JM3soi-XeLtbVi'

def send_push_notification(fcm_token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token,
    )

    response = messaging.send(message)
    print(f'Successfully sent message: {response}')

if __name__ == '__main__':
    send_push_notification(target_token, 'Sick Cow', 'A sick cow was detected in your pasture: https://goo.gl/maps/NLAx23bXNUmjpaz27')
