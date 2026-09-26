from database import add_message

def message_payload(message):
    if message.text:
        return "text", message.text
    if message.caption:
        return message.content_type, message.caption
    return message.content_type, None

def save_incoming(message, ticket_id, sender_type):
    message_type, text_value = message_payload(message)
    return add_message(
        ticket_id=ticket_id,
        sender_id=message.from_user.id,
        sender_type=sender_type,
        message_type=message_type,
        text_value=text_value,
        telegram_message_id=message.message_id,
    )
