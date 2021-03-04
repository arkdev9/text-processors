import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("app/data/fbadmin-key.json")
firebase_admin.initialize_app(cred)


def send_message(reg_token, title, body, data):
    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=reg_token,
    )
    response = messaging.send(message)
    # Response is a message ID string.
    return response
