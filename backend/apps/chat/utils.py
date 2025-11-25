from twilio.rest import Client
from decouple import config

def send_crisis_alert(user, chat_message):
    # Twilio configuration
    account_sid = config('TWILIO_ACCT_SID')
    auth_token = config('TWILIO_ACCT_AUTH_TOKEN')

    from_whatsapp_number = 'whatsapp:+14155238886'  # Replace with your Twilio WhatsApp number
    to_whatsapp_number = 'whatsapp:+2349025188065'     # Replace with the admin/support team's WhatsApp number

    client = Client(account_sid, auth_token)

    message_body = f"Crisis Alert!\nUser: {user.email}\nMessage: {chat_message.message}\nRisk Level: {chat_message.risk_level}\nUser's phone number: {user.phone_number if user.phone_number else 'null'}"

    message = client.messages.create(
        body=message_body,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    return message.sid
