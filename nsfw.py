from clarifai import rest
from clarifai.rest import ClarifaiApp
from clarifai.rest import Image as ClImage


def is_safe(image):
        app = ClarifaiApp()

        model = app.models.get('nsfw-v1.0')
        image = ClImage(url=image)
        output = model.predict([image])['outputs'][0]['data']['concepts']

        if output[0]['value'] > output[1]['value']:
                return True
        else:
                return False
