from flask import Flask, request
from flask_pymongo import PyMongo
from api import APICall
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
import json
import sentiment
import phrases
import validators
import website
import nsfw
import curse


app = Flask(__name__)
mongo = PyMongo(app)


PAGE_TOKEN = 'EAAZAdOvcHwZB8BABP56RMEr0X5SbikremIxomrVy1bU5GCeyptlvd0FALFybZCELKQTsC8FRWyIZB0BXPSdSmhNe8NAfLAZBOolTRhmGzwN5s40S9qfhFUefLRkVSMSFurw6P4bRAZAbqRBtAg9QpZBWIuLVh4Lm5sIPEY6BXFCBqh4gZBYEK2cr'
PAGE_ID = '2016014895300094'


fb = APICall(PAGE_TOKEN)


BASE_URL = 'https://9da4bf51.ngrok.io'


# nouns = {x.name().split('.', 1)[0] for x in wn.all_synsets('n')}


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


def get_image_message_parts(messaging):
    try:
        image = messaging[len(messaging) - 1]['message']['attachments'][0]
        if image['type'] == 'image':
            return image['payload']['url']
    except:
        return None


def get_text_message_parts(messaging):
    try:
        message = messaging[len(messaging) - 1]['message']['text']
        return message
    except:
        return None


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
                    if topic in user['topics'][i] or user['topics'][i] in topic:
                        if 'recipient' not in user or user['recipient'] == '':
                            return user['uid']
    return None



def is_url(message):
    parts = message.split()
    for part in parts:
        if validators.url(part):
            return True, part
    return False


def is_message_safe(message):
    if sentiment.is_positive(message):
        return True
    else:
        if curse.is_cursing(message):
            return False
        else:
            return True


def get_topics(message):
    # topics = []
    # keywords = phrases.get_key_phrases(message)
    # for keyword in keywords:
    #     topics.append(keyword)


    word_list = message.split()
    filtered_words = [word for word in word_list if word not in stopwords.words('english')]

    return filtered_words

    # for word in filtered_words:
    #     try:
    #         if word in nouns:
    #             # ws = wn.synsets(word)
    #             # for i in range(0, len(ws)):
    #             #     if i != 0:
    #             topics.append(word)
    #     except:
    #         print 'failed' 

    # return set(topics)
    # return keywords


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
                            topics = get_topics(message)
                            

                            mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'topics': topics}})

                            recipient = get_recipient(sender, topics)

                            if recipient is not None:
                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'recipient': recipient}})
                                mongo.db.ty.users.update_one({'uid': recipient}, {'$set': {'recipient': sender}})
                                send_to_recipient("You've been connected. Say Hi!", sender)
                                send_to_recipient("You've been connected. Say Hi!", recipient)
                            else:
                                if user['type'] == 'connect':
                                    send_to_recipient('Finding someone who can help you...', sender)
                                elif user['type'] == 'help':
                                    send_to_recipient('Finding someone you can help...', sender)
                            return '200'

                    else:

                        message = get_text_message_parts(messaging)
                        


                        if message != None:
                        
                            if message == 'stop':
                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'recipient': ''}})
                                send_to_recipient('You disconnected from the conversation.', sender)
                                mongo.db.ty.users.update_one({'uid': user['recipient']}, {'$set': {'recipient': ''}})
                                send_to_recipient('You have been disconnected from the conversation.', user['recipient'])
                            elif message == 'restart':
                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'type': '', 'topics': '', 'recipient': ''}})
                                
                                if 'recipient' in user:
                                    send_to_recipient('You disconnected from the conversation.', sender)
                                    mongo.db.ty.users.update_one({'uid': user['recipient']}, {'$set': {'recipient': ''}})
                                    send_to_recipient('You have been disconnected from the conversation.', user['recipient'])
                                else:
                                    send_to_recipient('Your profile has been reset.', sender)
                                send_welcome_message(sender)
                            elif is_url(message) != False:
                                x, url = is_url(message)
                                if website.is_nsfw(url):
                                    send_to_recipient('Explicit content detected. Message blocked.', sender)
                                else:
                                    send_to_recipient(message, user['recipient'])
                                return '200'
                            else:
                                if is_message_safe(message):
                                    send_to_recipient(message, user['recipient'])
                                else:
                                    send_to_recipient('Explicit content detected. Message blocked.', sender)
                                return ' 200'

                        else:
                            url = get_image_message_parts(messaging)

                            if url != None:
                                if nsfw.is_safe(url):
                                    send_to_recipient(url, user['recipient'])
                                else:
                                    send_to_recipient('Explicit content detected. Message blocked.', sender)
                                return '200'
                            
            return '200'




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)