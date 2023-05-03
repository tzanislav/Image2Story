from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

from array import array
import os
from PIL import Image
import requests
from io import BytesIO
from urllib.parse import urlparse
import sys
import time
import azure.cognitiveservices.speech as speechsdk
import pygame
import openai


'''
Authenticate
Authenticates your credentials and creates a client.
'''

openai.api_key = "YOUR-OPENAI-KEY"  

subscription_key = "YOUR-AZURE-API-KEY"
endpoint = "YOUR-AZURE-ENDPOINT"

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

speech_key = 'YOUR-SPEECH-RESOURCE-KEY'
service_region = 'westeurope'
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "en-US-DavisNeural"
'''
END - Authenticate
'''


def OCR (url):
    '''
    OCR: Read File using the Read API, extract text - remote
    This example will extract text in an image, then print results, line by line.
    This API call can also extract handwriting style text (not shown).
    '''
    print("===== Read File - remote =====")
    # Get an image with text
    read_image_url = url

    # Call API with URL and raw response (allows you to get the operation location)
    read_response = computervision_client.read(read_image_url,  raw=True)

    # Get the operation location (URL with an ID at the end) from the response
    read_operation_location = read_response.headers["Operation-Location"]
    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]

    # Call the "GET" API and wait for it to retrieve the results 
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Print the detected text, line by line
    result = ""

    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
              #  print(line.text)
              #  print(line.bounding_box)
                result += line.text + " "

    return result

def ImageRecognize (url):

    textInImage = OCR(inputText)

    '''
    Quickstart variables
    These variables are shared by several examples
    '''
    # Images used for the examples: Describe an image, Categorize an image, Tag an image, 
    # Detect faces, Detect adult or racy content, Detect the color scheme, 
    # Detect domain-specific content, Detect image types, Detect objects
    # images_folder = os.path.join (os.path.dirname(os.path.abspath(__file__)), "images")
    remote_image_url = url
    '''
    END - Quickstart variables
    '''


    '''
    Tag an Image - remote
    This example returns a tag (key word) for each thing in the image.
    '''
    print("===== Tag an image - remote =====")
    # Call API with remote image
    tags_result_remote = computervision_client.tag_image(remote_image_url )

    # Print results with confidence score
    print("Tags in the remote image: ")
    if (len(tags_result_remote.tags) == 0):
        print("No tags detected.")
    else:
        output = "'"
        for tag in tags_result_remote.tags:
            print("'{}' with confidence {:.2f}%".format(tag.name, tag.confidence * 100))
            output += tag.name + ", "
        output += "'"

            
    print("Output: '{}' /n Text in image: {}".format(output, textInImage))

    if(input("Use text in images? y/n  ") != "y"):
        textInImage = ""

    addition = input("Additional words: ")



    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Describe a scene based on these words '{} {} {}'. Don't mention people if they are not in the word set. Ignore the word 'Human' ".format(output, addition, textInImage)}
        ]
    )

    print(completion.choices[0].message.content)

    Speak(completion.choices[0].message.content)
    
    print()
    '''
    END - Tag an Image - remote
    '''
    print("End of Computer Vision quickstart.")

def Speak(text):

    print("Synthesizing speech")

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    text_to_synthesize = text
    result = speech_synthesizer.speak_text_async(text_to_synthesize).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data

        with open('output_audio.wav', 'wb') as audio_file:
            audio_file.write(audio_data)

        pygame.init()
        audio_filename = 'output_audio.wav'

        pygame.mixer.music.load(audio_filename)

        # Wait for the user to press a key to interrupt the playback
        input("Press any key to stop playback...")

        # Stop the playback
        pygame.mixer.music.stop()

        # Clean up the mixer
        pygame.mixer.quit()

    


while(1):
    inputText = input("Enter URL:  ")

    try:
        result = urlparse(inputText)
        if all([result.scheme, result.netloc]):
            print("Valid URL")
            response = requests.get(inputText)
            image_data = BytesIO(response.content)

            try:
                image = Image.open(image_data)
            except IOError:
                print("The URL does not point to a valid image file.")
            else:
                print("The URL points to a valid image file.")
                ImageRecognize(inputText)

        else:
            print("Invalid URL")
    except ValueError:
        print("Invalid URL")


