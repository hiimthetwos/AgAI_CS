import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth, messaging
from firebase_admin import firestore

cred = credentials.Certificate('/home/ryanbert/Documents/firebase.json')
firebase_admin.initialize_app(cred)

def send_notification_to_email(email, title, body):
    try:
        # Get the user record by email
        user = auth.get_user_by_email(email)

        # Get the FCM token from Firestore
        user_doc = firestore.client().collection('users').document(user.uid).get()
        fcm_token = user_doc.get("fcmToken")

        if fcm_token is None:
            print(f'Error: FCM token not found for user {email}')
            return

        # Compose the notification
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )

        # Send the notification
        response = messaging.send(message)
        print(f'Successfully sent message: {response}')

    except Exception as e:
        print(f'Error fetching user data or sending notification: {e}')


email = 'ryanbert@gmail.com'
title = 'Notification Title'
body = 'Notification Body'
