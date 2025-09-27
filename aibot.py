import os, pyaudio, gc
from threading import Thread
from openai import OpenAI
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import numpy as np
from time import sleep, time
import subprocess
import cv2
import base64
from picamera2 import Picamera2
import RPi.GPIO as GPIO

########################--GLOBAL VARIABLES-################################	
language = 'en'
client = OpenAI(api_key= '[INSERT API KEY]')

messages = [{'role': 'developer', 'content': 'You move 12 inches by saying one of the commands at a time: 
            forward, reverse, left, or right, by you, not the user. You are 6 inches tall and 8 inches wide. 
            Explore and avoid colliding by judging the distance, but first, respond to the user messages concisely.'}]
            
images = [{'role': 'developer', 'content': 'Filler element.'}]
greetings = ["Hello, What can I do for you?",
             "How can I help?",
             "Hey, How's it going?",
             "Nice to meet you."]

wait_msg = " Please wait. I am thinking."
r = sr.Recognizer()

unmute_command = ["amixer", "sset", "'Capture'", "cap"]
mute_command = ["amixer", "sset", "'Capture'", "nocap"]

#Camera Initialisation
image_path = '/home/user/image.jpg'
cam = Picamera2()
camera_config = cam.create_still_configuration(main={'size':(1920, 1080)}, lores={'size':(640, 480)}, display='lores')
cam.configure(camera_config)
#picam2.start_preview(Preview.QTGL)

#Pin Allocation and Wheel Control Initialisation 
GPIO.setmode(GPIO.BCM)	
#Left wheel
GPIO.setup(18, GPIO.OUT) #Enable
GPIO.setup(23, GPIO.OUT)	
GPIO.setup(24, GPIO.OUT)
#Right wheel
GPIO.setup(4, GPIO.OUT) #Enable
GPIO.setup(17, GPIO.OUT)	
GPIO.setup(27, GPIO.OUT)

left_pwm = GPIO.PWM(18, 1000)
right_pwm = GPIO.PWM(4, 1000)

duty_cycle = 100
	
########################--GENERAL FUNCTIONS--################################	
def deallocate(memory, max_len):
	if len(memory) == max_len:
		i = len(memory)
		while len(memory) > 1:
			memory.pop(i-1)
			i = i - 1
		gc.collect()
	
def ai_response(messages):
	completion= client.chat.completions.create(
		model= 'gpt-4.1',
		messages= messages,
	)
	return completion.choices[0].message.content

########################--AUDIO FUNCTIONS--################################
def say(text):
	tts = gTTS(text)
	tts.save('response.mp3')
	playsound('response.mp3')

/*
 * Title:  chatGPT-Voice-Assistant by Thomas Vu Nguyen
 * Author: Thomas Vu Nguyen
 * Date:   16 June 2025
 * Code version: N/A
 * Type: Source Code
 * Availability: https://github.com/ThomasVuNguyen/chatGPT-Voice-Assistant
 */
// Start of cited code

def wait_for_silence(source):
	while True:
		audio = r.listen(source)
		try:
			text = r.recognize_google(audio)
			print(text)
		except  sr.UnknownValueError:
			try: 
				#print('test')
				pass
			finally:
				break
		except sr.RequestError as e:
			try:
				pass
			finally:
				break

def wake_word(source):
	#print('Listening for trigger word...')
	say('hi')
	text = 'placeholder'
	while not ('hello' in text.lower()):
		audio = r.listen(source)
		try:
			text = r.recognize_google(audio)
			print(f'{text}')
		except sr.UnknownValueError:
			pass
	#print('Trigger word detected.')
	subprocess.Popen(mute_command)
	greet= gTTS(text=np.random.choice(greetings),lang=language)
	greet.save('response.mp3')
	playsound('response.mp3')
	subprocess.Popen(unmute_command)

def converse(source):
	time1 = time()
	#print('Listening...')
	while True:
		time2 = time()
		#To allocate memory for new list once memory is de-allocated
		audio = r.listen(source)
		try:
			text = r.recognize_google(audio)
			#print(f'You said: {text}')
			
			#Append the image to the messages list.
			messages.append(images[len(images)-1])
			#Append the response to the messages list.
			messages.append({'role':'user', 'content':text})
			
			subprocess.Popen(mute_command)
			say(wait_msg)
			subprocess.Popen(unmute_command)
			
			#Send input to OpenAI API
			#print(ai_response(messages))
			subprocess.Popen(mute_command)
			say(ai_response(messages))
			subprocess.Popen(unmute_command)
			
			#Waits until the AI stop talking to prevent self responding.
			wait_for_silence(source)
			
			#Makes AI control the wheels.
			move(ai_response(messages))
			
			time1 = time()
			
			#Pop the image out the messages list to prevent rate limit errors and save tokens.
			messages.pop(len(messages)-1)
			
			#To de-allocate memory
			deallocate(messages, 100)
		
			if not audio:
				playsound("error.mp3")
	
		except sr.UnknownValueError:
			#Goes back to sleep after some time not receiving audio input.
			diff = time2 - time1
			if diff >= 1800: #20 minutes
				playsound("error.mp3")
				break
			pass
						
		except sr.WaitTimeoutError:
			try:
				print("Silence detected. Shutting up")
			finally:
				break
				
		except sr.RequestError as e:
			try:
				print(f"Could not request results; {e}")
				
				subprocess.Popen(mute_command)
				engine.say(f"Could not request results; {e}")
				subprocess.Popen(unmute_command)
			finally:
				pass

// End of cited code

########################--VISION FUNCTIONS--################################	
def encode_image(image_path):
	with open(image_path, 'rb') as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')

########################--WHEEL CONTROL FUNCTIONS--################################	
def forward_right():
	left_pwm.start(duty_cycle)
	GPIO.output(23, GPIO.HIGH)
	GPIO.output(24, GPIO.LOW)
	
def reverse_right():
	left_pwm.start(duty_cycle)
	GPIO.output(23, GPIO.LOW)
	GPIO.output(24, GPIO.HIGH)
	
def stop_right():
	left_pwm.start(0)
	GPIO.output(23, GPIO.LOW)
	GPIO.output(24, GPIO.LOW)
			
def forward_left():
	right_pwm.start(duty_cycle)
	GPIO.output(17, GPIO.HIGH)
	GPIO.output(27, GPIO.LOW)
	
def reverse_left():
	right_pwm.start(duty_cycle)
	GPIO.output(17, GPIO.LOW)
	GPIO.output(27, GPIO.HIGH)
	
def stop_left():
	right_pwm.start(0)
	GPIO.output(17, GPIO.LOW)
	GPIO.output(27, GPIO.LOW)
	
def forward():
	forward_right()
	forward_left()

def reverse():
	reverse_right()
	reverse_left()

def left():
	stop_left()
	forward_right()

def right():
	forward_left()
	stop_right()

def stop():
	stop_right()
	stop_left()

def move(text):
	if 'forward' in text.lower():
		forward()
		sleep(1)
		stop()
	elif 'reverse' in text.lower():
		reverse()
		sleep(1)
		stop()
	elif 'right' in text.lower():
		right()
		sleep(1)
		stop()
	elif 'left' in text.lower():
		left()
		sleep(1)
		stop()
	elif 'stop' in text.lower():
		stop()
		
########################--THREADS--################################		
def audio_process():
	while True:
		with sr.Microphone() as source:
			wake_word(source)
			converse(source)
			
def vision_process():
	cam.start()
	while True:
		sleep(10)
		#print('Capturing...')
		#Captures the image into the images list.
		cam.capture_file('image.jpg')
		base64_image = encode_image(image_path)
		images.append({'role':'user', 'content':[{'type':'image_url', 'image_url':{'url':f'data:image/jpeg;base64,{base64_image}'}}]})
		
		#Append image to the messages list.
		messages.append(images[len(images)-1])
		#print(ai_response(messages))
		
		#Makes AI control the wheels.
		move(ai_response(messages))
		
		#Pop image out the messages list to prevent rate limit errors and save tokens.
		messages.pop(len(messages)-1)
		
		#To de-allocate memory
		deallocate(messages, 100)
	cam.stop()
	
########################--MAIN THREAD--################################		
def main():	
	audio_thread = Thread(target= audio_process)
	vision_thread = Thread(target= vision_process)
	
	sleep(40)
	audio_thread.start()
	vision_thread.start()
	while True:
		pass
		

if __name__=="__main__":
    main()


