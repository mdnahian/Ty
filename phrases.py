import httplib, urllib
import json


accessKey = '57233889fb354b4eb1e30e5eeac0fb7c'


uri = 'eastus2.api.cognitive.microsoft.com'
path = '/text/analytics/v2.0/keyPhrases'

def get_key_phrases (text):
    
    documents = { 'documents': [
        { 'id': '1', 'language': 'en', 'text': text }
    ]}
    headers = {'Ocp-Apim-Subscription-Key': accessKey}
    conn = httplib.HTTPSConnection (uri)
    body = json.dumps (documents)
    conn.request ("POST", path, body, headers)
    response = conn.getresponse ()
    keyPhrases = json.loads(response.read())['documents'][0]['keyPhrases']
    return keyPhrases