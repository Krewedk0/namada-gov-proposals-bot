from telegram.ext import Updater, CommandHandler, PicklePersistence, CallbackContext
from telegram import Chat, Update
from utils import get_current_epoch, query_proposals, format_notification
import logging
import os

MAX_MESSAGE_LENGTH = 4090
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def list_active_proposals(update: Update, context: CallbackContext):
    chat = update.effective_chat
    proposals = context.bot_data.get('proposals_data', set()).copy()
    try:
        current_epoch = get_current_epoch()
    except Exception as e:
        logging.error(f'Failed to get current epoch: {e}')
        context.bot.send_message(text='Failed to get current epoch', chat_id=chat.id)
        return
    
    props = []
    for id, proposal in proposals.items():
        start = int(proposal['Start Epoch'])
        end = int(proposal['End Epoch'])
        if start <= current_epoch and current_epoch <= end:
            title = proposal['Content'].get('title')
            props.append(f'#{id} (ends on start of epoch {end+1}): {title}\n\n')
    
    messages = []
    if props:
        props_text = f"Current epoch: {current_epoch}; Active proposals:\n\n"
        for prop in props:
            if len(props_text) + len(prop) > MAX_MESSAGE_LENGTH:
                messages.append(props_text)
                props_text = prop
            else:
                props_text += prop
        messages.append(props_text)
    else:
        messages.append(f"There are no active proposals in the current ({current_epoch}) epoch")
    
    for msg in messages:
        context.bot.send_message(text=msg, chat_id=chat.id)

def notify_subscribed_users(bot, messages, subscribed_users):
    for user_id in subscribed_users:
        for message in messages:
            try:
                bot.send_message(user_id, message)
            except Exception as e:
                logging.error(f'Failed to send notification to user {user_id}: {e}')


def start(update: Update, context: CallbackContext) -> None:    
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE:
        return
    
    user_id = update.message.from_user.id
    context.bot_data.setdefault("user_ids", set()).add(user_id)

    text = "Successfully subscribed for SE governance proposals"
    logging.info(f'New user subscribed - {user_id}')

    context.bot.send_message(text=text, chat_id=chat.id)


# Function to periodically check for new proposals
def check_new_proposals(context: CallbackContext):
    if not context.bot_data.get("proposals"):
        context.bot_data["proposals"] = set()
    if not context.bot_data.get("notifications"):
        context.bot_data["notifications"] = set()
    if not context.bot_data.get("proposals_data"):
        context.bot_data["proposals_data"] = {}
    
    notifications = context.bot_data["notifications"]
    proposals_data = context.bot_data["proposals_data"]
    proposals = context.bot_data["proposals"]
    current_epoch = get_current_epoch()
    if len(proposals) == 0:
        latest = 0
    else:
        latest = max(proposals)
    
    try:
        new_proposals = query_proposals(latest)
    except Exception as e:
        logging.error(f'Failed to fetch proposals: {e}')
        return
    
    for prop in new_proposals:
        id = int(prop['Proposal Id'])
        if id not in proposals_data:
            proposals_data[id] = prop
    
    messages = []
    current_message = ''
    for id, proposal in proposals_data.items():
        proposals.add(id)
        start = int(proposal['Start Epoch'])
        if id in notifications or start != current_epoch:
            continue

        logging.info(f'sending notifications for prop #{id}')
        notifications.add(id)
        
        notification_text = format_notification(proposal)
        if len(current_message) + len(notification_text) > MAX_MESSAGE_LENGTH:
            messages.append(current_message)
            current_message = notification_text
        else:
            current_message += f'{notification_text}\n\n'
        
    if messages or current_message:
        messages.append(current_message)
        users = context.bot_data.get('user_ids', set()).copy()
        notify_subscribed_users(context.bot, messages, users)


def main():
    persistence = PicklePersistence(filename='data.pickle')
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logging.error('No bot token provided (BOT_TOKEN env var), exiting')
        return
    
    updater = Updater(bot_token, use_context=True, persistence=persistence)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("proposals", list_active_proposals))

    updater.start_polling()
    updater.job_queue.run_repeating(check_new_proposals, interval=60, first=3)
    updater.idle()

if __name__ == '__main__':
    main()