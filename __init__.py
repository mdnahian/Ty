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


BASE_URL = 'https://ab28966b.ngrok.io'


# nouns = {x.name().split('.', 1)[0] for x in wn.all_synsets('n')}




def get_synonyms(word):
        synonyms = []
        for synset in wn.synsets(word):
                for lemma in synset.lemmas():
                        synonyms.append(lemma.name())
        return synonyms




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
                            "title": "Learn"
                        },
                        {
                            "type": "web_url",
                            "url": BASE_URL+"/type/help/"+user_id,
                            "title": "Teach"
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


@app.route('/delete')
def delete():
    users = mongo.db.ty.users.find({})
    for user in users:
        mongo.db.ty.users.delete_one({'uid': user['uid']})
    return '200'


def get_text_message_parts(messaging):
    try:
        message = messaging[len(messaging) - 1]['message']['text']
        return message
    except:
        return None


def send_welcome_message(sender):
    send_to_recipient("Hi, I'm Ty. I can connect you to people who have similar interests to promote a healthy environment for discussion.", sender)
    send_button_to_user(sender)


@app.route('/type/<t>/<uid>', methods=['GET'])
def type(t, uid):
    user = mongo.db.ty.users.find_one({'uid': uid})

    if user is not None:
        if t == 'connect':
            mongo.db.ty.users.update_one({'uid': uid}, {'$set': {'type': t}})
            send_to_recipient('What would you like to learn about?', uid)
        elif t == 'help':
            mongo.db.ty.users.update_one({'uid': uid}, {'$set': {'type': t}})
            send_to_recipient('What do you know about?', uid)

    return '<script>window.close();</script>'




def get_recipient(user_id, topics):
    users = mongo.db.ty.users.find()
    for user in users:
        if user['uid'] != user_id:
            if 'topics' in user:
                for i in range(0, len(user['topics'])):
                    print i
                    for topic in topics:
                        if topic.lower().replace('_', ' ') in user['topics'][i].lower().replace('_', ' ') or user['topics'][i].lower().replace('_', ' ') in topic.lower().replace('_', ' '):
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
    topics = []
    # keywords = phrases.get_key_phrases(message)
    # for keyword in keywords:
    #     topics.append(keyword)


    word_list = message.split()
    print word_list
    for word in word_list:
        if len(word) > 4:
            synonyms = get_synonyms(word)
            for synonym in synonyms:
                if len(synonym) >= 4:
                    topics.append(synonym)
    # return word_list
    #filtered_words = [word for word in word_list if word not in stopwords.words('english')]

    #return filtered_words

    # for word in filtered_words:
    #     try:
    #         if word in nouns:
    #             # ws = wn.synsets(word)
    #             # for i in range(0, len(ws)):
    #             #     if i != 0:
    #             topics.append(word)
    #     except:
    #         print 'failed' 

    return topics
    # return keywords


@app.route('/', methods=['GET', 'POST'])
def webhook():
    #return request.args.get('hub.challenge', '')
    if request.method == 'POST':
        response = request.get_json()

        if response['object'] == 'page':


            sender, messaging = get_sender(response)

            user = mongo.db.ty.users.find_one({'uid': sender})

            print user

            if sender != PAGE_ID:

                if user is None:
                    mongo.db.ty.users.insert_one({
                        'uid': sender
                    })
                    send_welcome_message(sender)
                    return '200'
                else:
                    if 'recipient' not in user:
                        if 'type' not in user or len(user['type'])==0:
                            return '200'
                        else:
                            message = get_text_message_parts(messaging)

                            if message is not None:
                                message.replace('.', '').replace('?', '')
                                topics = get_topics(message)
                                
                                print topics

                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'topics': topics}})

                                recipient = get_recipient(sender, topics)

                                if recipient is not None:
                                    mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'recipient': recipient}})
                                    mongo.db.ty.users.update_one({'uid': recipient}, {'$set': {'recipient': sender}})
                                    send_to_recipient("You've been connected. Say Hi!", sender)
                                    send_to_recipient("You've been connected. Say Hi!", recipient)
                                else:
                                    print user
                                    if user['type'] == 'connect':
                                        send_to_recipient('Finding someone with similar interests...', sender)
                                    elif user['type'] == 'help':
                                        send_to_recipient('Finding someone with similar interests...', sender)
                                return '200'

                            return '200'

                    else:

                        message = get_text_message_parts(messaging)                        


                        if message != None:

                            message = message.replace('.', '').replace('?', '')
                        
                            if message.lower() == 'stop':
                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'recipient': ''}})
                                send_to_recipient('You disconnected from the conversation.', sender)
                                mongo.db.ty.users.update_one({'uid': user['recipient']}, {'$set': {'recipient': ''}})
                                send_to_recipient('You have been disconnected from the conversation.', user['recipient'])
                            elif message.lower() == 'restart':
                                mongo.db.ty.users.update_one({'uid': sender}, {'$set': {'type': '', 'topics': '', 'recipient': ''}})
                                
                                if 'recipient' in user:
                                    send_to_recipient('You disconnected from the conversation.', sender)
                                    mongo.db.ty.users.update_one({'uid': user['recipient']}, {'$set': {'recipient': ''}})
                                    send_to_recipient('You have been disconnected from the conversation.', user['recipient'])
                                else:
                                    send_to_recipient('Your profile has been reset.', sender)

                                mongo.db.ty.users.delete_one({'uid': user['recipient']})
                                mongo.db.ty.users.delete_one({'uid': sender})
                                # send_welcome_message(sender)
                            elif is_url(message) != False:
                                x, url = is_url(message)
                                if website.is_nsfw(url):
                                    send_to_recipient('Explicit content detected. Message blocked.', sender)
                                else:
                                    send_to_recipient(message, user['recipient'])
                                return '200'
                            else:
                                if is_message_safe(message):



                                    recipient = mongo.db.ty.users.find_one({'uid': user['recipient']})
                                    
                                    recipient_topics = recipient['topics']
                                    user_topics = user['topics']

                                    topics = []
                                    topics.extend(recipient_topics)
                                    topics.extend(user_topics)

                                    message_topics = get_topics(message)

                                    if message_topics is not None:
                                        if 'session' in user:
                                            message_topics.extend(user['session'])
                                            mongo.db.ty.users.update_one({'uid': user['uid']}, {'$set': {'session': message_topics}})
                                        else:
                                            mongo.db.ty.users.update_one({'uid': user['uid']}, {'$set': {'session': message_topics}})


                                    print message_topics

                                    score = 0

                                    for topic in topics:
                                        topic_lemmas = wn.synsets(topic)[0]
                                        for mtopic in message_topics:
                                            mtopic_lemmas = wn.synsets(mtopic)[0]

                                            
                                            x = topic_lemmas.path_similarity(mtopic_lemmas)

                                            if x is not None:
                                                score += x



                                    total_score = score/len(topics)

                                    print total_score


                                    if total_score > 4 and total_score < 10:
                                        send_to_recipient('Conversation has gone out of topic.', sender)
                                        
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
    return '200'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
