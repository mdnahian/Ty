from flask import Flask, request
from flask_pymongo import PyMongo
from api import APICall
import json


app = Flask(__name__)
mongo = PyMongo(app)


PAGE_TOKEN = 'EAAZAdOvcHwZB8BABP56RMEr0X5SbikremIxomrVy1bU5GCeyptlvd0FALFybZCELKQTsC8FRWyIZB0BXPSdSmhNe8NAfLAZBOolTRhmGzwN5s40S9qfhFUefLRkVSMSFurw6P4bRAZAbqRBtAg9QpZBWIuLVh4Lm5sIPEY6BXFCBqh4gZBYEK2cr'
PAGE_ID = '2016014895300094'


fb = APICall(PAGE_TOKEN)


BASE_URL = 'https://084137d5.ngrok.io'


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
                            "url": BASE_URL+"/connect",
                            "title": "Connect With Someone"
                        },
                        {
                            "type": "web_url",
                            "url": BASE_URL+"/help",
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


def get_user_name(sender):
    link = 'https://graph.facebook.com/v2.8/' + sender
    response = fb.makeRequest(link)
    return json.loads(response)['first_name']


def send_welcome_message(sender):
    send_to_recipient("Hello, I'm Ty. I can connect you with someone who can help you.", sender)
    send_button_to_user(sender)


@app.route('/connect', method=['POST'])
def connect():
    if request.method == 'POST':
        response = request.get_json()
        print response


@app.route('/', methods=['GET', 'POST'])
def webhook():
    # return request.args.get('hub.challenge', '')
    if request.method == 'POST':
        response = request.get_json()

        if response['object'] == 'page':
            sender, messaging = get_sender(response)

            user = mongo.db.users.find({'uid': sender})

            if user is None:
                name = get_user_name()
                mongo.db.users.insert({
                    'name': name,
                    'uid': sender
                })
                send_welcome_message(sender)
                return '200'



            message = get_text_message_parts(messaging)



        return '200'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)