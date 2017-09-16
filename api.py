import requests
import json


class APICall:
    def __init__(self, access_token):
        self.access_token = access_token

    def makeRequest(self, url):
        url = url + '?access_token=' + self.access_token
        # print url
        return requests.get(url).text

    def makeRequestPost(self, url, data):
        url = url + '?access_token=' + self.access_token
        # print url
        return requests.post(url, json=json.loads(json.dumps(data))).text