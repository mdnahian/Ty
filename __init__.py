from flask import Flask, request
from flask_pymongo import PyMongo
from api import APICall
import json
import sentiment
import phrases


app = Flask(__name__)
mongo = PyMongo(app)


PAGE_TOKEN = 'EAAZAdOvcHwZB8BABP56RMEr0X5SbikremIxomrVy1bU5GCeyptlvd0FALFybZCELKQTsC8FRWyIZB0BXPSdSmhNe8NAfLAZBOolTRhmGzwN5s40S9qfhFUefLRkVSMSFurw6P4bRAZAbqRBtAg9QpZBWIuLVh4Lm5sIPEY6BXFCBqh4gZBYEK2cr'
PAGE_ID = '2016014895300094'


fb = APICall(PAGE_TOKEN)


BASE_URL = 'https://9da4bf51.ngrok.io'


def send_button_to_user(user_id):
    link = 'https://graph.facebook.com/v2.6/' + PAGE_ID + '/messages'
    data = {
        "recipient": {
            "id": user_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "What would you like to do?",
                    "buttons": [
                        {
                            "type": "web_url",
                            "url": BASE_URL+"/type/connect/"+user_id,
                            "title": "Connect With Someone"
                        },
                        {
                            "type": "web_url",
                            "url": BASE_URL+"/type/help/"+user_id,
                            "title": "Help Someone"
                        }
                    ]
                }
            }
        }
    }
    print fb.makeRequestPost(link, data)


def send_to_recipient(message, user_id):
    link = 'https://graph.facebook.com/v2.6/' + PAGE_ID + '/messages'
    data = {
        "recipient": {
            "id": user_id
        },
        "message": {
            "text": message
        }
    }
    print fb.makeRequestPost(link, data)


def get_sender(response):
    entries = response['entry']
    messaging = entries[len(entries) - 1]['messaging']
    return messaging[len(messaging) - 1]['sender']['id'], messaging


def get_text_message_parts(messaging):
    message = messaging[len(messaging) - 1]['message']['text']
    return message


def send_welcome_message(sender):
    send_to_recipient("Hello, I'm Ty. I can connect you with someone who can help you.", sender)
    send_button_to_user(sender)


@app.route('/type/<t>/<uid>', methods=['GET'])
def type(t, uid):
    user = mongo.db.ty.users.find_one({'uid': uid})

    if user is not None:
        if t == 'connect':
            mongo.db.ty.users.update_one({'uid': uid}, {'$set': {'type': t}})
            send_to_recipient('What do you need help with?', uid)
        elif t == 'help':
            mongo.db.ty.users.update_one({'uid': uid}, {'$set': {'type': t}})
            send_to_recipient('What can you help with?', uid)

    return '<script>window.close();</script>'




def get_recipient(user_id, topics):
    users = mongo.db.ty.users.find()
    for user in users:
        if user['uid'] != user_id:
            for i in range(0, len(user['topics'])):
                for topic in topics:
                    if topic == user['topics'][i]:
                        if 'recipient' not in user or user['recipient'] == '':
                            return user['uid']
    return None





@app.route('/', methods=['GET', 'POST'])
def webhook():
    #return request.args.get('hub.challenge', '')
    if request.method == 'POST':
        response = request.get_json()

        if response['object'] == 'page':
            sender, messaging = get_sender(response)

            user = mongo.db.ty.users.find_one({'uid': sender})

            if sender != PAGE_ID:

                if user is None:
                    mongo.db.ty.users.insert_one({
                        'uid': sender
                    })
                    send_welcome_message(sender)
                    return '200'
                else:
                    if 'recipient' not in user:
                        if 'type' not in user:
                            return '200'
                        else:
                            message = get_text_message_parts(messaging)
                            print message
                            topics = phrases.get_key_phrases(message)
                            print topics

                            mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'topics': topics}})

                            recipient = get_recipient(sender, topics)

                            if recipient is not None:
                                mongo.db.ty.users.update_one({'uid': uid}, {'$set': {'recipient': recipient}})
                                send_to_recipient("You've been connected. Say Hi!")
                            else:
                                if user['type'] == 'connect':
                                    send_to_recipient('Finding someone who can help you...', sender)
                                elif user['type'] == 'help':
                                    send_to_recipient('Finding someone you can help...', sender)
                            return '200'

                    else:
                        message = get_text_message_parts(messaging)
                        if message == 'stop':
                            mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'recipient': ''}})
                            mongo.db.ty.users.update_one({'uid': user['recipient']}, {'$set': {'recipient': ''}})
                        elif message == 'restart':
                            mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'type': '', 'topics': '', 'recipient': ''}})
                            send_welcome_message(sender)
                        else:
                            if sentiment.is_positive(message):
                                send_to_recipient(message, user['recipient'])
                                return '200'
                            else:
                                send_to_recipient('Explicit content detected. Message blocked.', sender)
                                return ' 200'

                            

            return '200'




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)