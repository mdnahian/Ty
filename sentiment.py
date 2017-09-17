import httplib, urllib
import json


def is_positive(text):
    accessKey = '57233889fb354b4eb1e30e5eeac0fb7c'


    uri = 'eastus2.api.cognitive.microsoft.com'
    path = '/text/analytics/v2.0/sentiment'

    
    documents = { 'documents': [
        { 'id': '1', 'language': 'en', 'text': text}
    ]}

    headers = {'Ocp-Apim-Subscription-Key': accessKey}
    conn = httplib.HTTPSConnection (uri)
    body = json.dumps (documents)
    conn.request ("POST", path, body, headers)
    response = conn.getresponse ()
    score = json.loads(response.read())['documents'][0]['score']

    if score > 0.7:
        return True
    else:
        return False