#!/usr/bin/env python2
#
# Example to compare the faces in two images.
# Brandon Amos
# 2015/09/29
#
# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	 http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import cv2
import itertools
import os
from os import listdir
from os.path import isfile, join ,isdir
import numpy as np
np.set_printoptions(precision=2)
import openface

import urllib2
import urllib
import requests
import json
import time
import sys
from threading import Thread, Lock
import traceback
import socket
from socketIO_client import SocketIO, BaseNamespace
# load datetime in the end
import datetime
def system_execute(_command):
	process = subprocess.Popen(_command, stdout=subprocess.PIPE, shell=True)
	while True:
		if process.poll() is not None:
			break
	return process.stdout.readlines()

def print_error(e):
	print "*************Error*************"
	print str(e)
	traceback.print_stack()
	print "*******************************"

mutex_datetime = Lock()

def get_datetime_format():
	return "%b-%d-%y %I:%M:%S%p"

def get_date_format():
	return "%b-%d-%y"

def get_datetime_from_str(_str):
	global mutex_datetime
	mutex_datetime.acquire()
	return_val =""
	try:
		return_val= datetime.datetime.strptime(_str,get_datetime_format())
	except Exception as e:
		print_error(e)
		pass
	mutex_datetime.release()
	return return_val

def get_str_from_datetime(_datetime):
	global mutex_datetime
	mutex_datetime.acquire()
	return_val =""
	try:
		return_val= _datetime.strftime(get_datetime_format())
	except Exception as e:
		print_error(e)
		pass
	mutex_datetime.release()
	return return_val

def get_date_from_str(_str):
	parsed_date = get_datetime_from_str(_str)
	global mutex_datetime
	mutex_datetime.acquire()
	return_val =""
	try:
		return_val= datetime.datetime(year=parsed_date.year,month=parsed_date.month,day=parsed_date.day)
	except Exception as e:
		print_error(e)
		pass
	mutex_datetime.release()
	return return_val

def get_date_str_from_datetime_str(_str):
	date = get_date_from_str(_str)
	global mutex_datetime
	mutex_datetime.acquire()
	return_val =""
	try:
		return_val= date.strftime("%b-%d-%y")
	except Exception as e:
		print_error(e)
		pass
	mutex_datetime.release()
	return return_val

def get_current_time_str():
	global mutex_datetime
	mutex_datetime.acquire()
	return_val =""
	try:
		return_val= datetime.datetime.now().strftime(get_datetime_format())
	except Exception as e:
		print_error(e)
		pass
	mutex_datetime.release()
	return return_val

def log_status(_msg):
	print '['+get_current_time_str()+'] '+_msg

def create_directories(_directory):
	if not os.path.exists(_directory):
		os.makedirs(_directory)
#------------------------end of common methods-----------------------


fileDir = os.path.dirname(os.path.realpath(__file__))
modelDir = os.path.join(fileDir, '..', 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
dlibFacePredictor =os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat")
openfaceModelDir = os.path.join(modelDir, 'openface')
networkModel = os.path.join(openfaceModelDir, 'nn4.small2.v1.t7')
imgs_recorded_dir= join(fileDir,'recorded_data')

imgDim=96

align = openface.AlignDlib(dlibFacePredictor)
net = openface.TorchNeuralNet(networkModel, imgDim)
recorded_data = []

def getRep(imgPath):

	print("Processing {}.".format(imgPath))
	bgrImg = cv2.imread(imgPath)
	if bgrImg is None:
		raise Exception("Unable to load image: {}".format(imgPath))
	rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

	# face detection
	bb = align.getLargestFaceBoundingBox(rgbImg)
	if bb is None:
		raise Exception("Unable to find a face: {}".format(imgPath))

	# face alignment
	alignedFace = align.align(imgDim, rgbImg, bb,
							  landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
	if alignedFace is None:
		raise Exception("Unable to align image: {}".format(imgPath))

	# face representation
	rep = net.forward(alignedFace)
	return rep

def get_files_in_dir(_dir):
	files= [join(_dir, f) for f in listdir(_dir) if isfile(join(_dir f))]
	return files

def get_dir_names_in_dir(_dir):
	dirs = [f for f in listdir(_dir) if isdir(join(_dir, f))]
	return dirs

def get_representation_from_dir(_dir):
	representation =[]
	files = get_files_in_dir(_dir)
	for f in files:
		r = getRep(f)
		representation.append(r)
	return representation

def add_dir_representation_to_record(_base_dir,_name):
	dir_path =join(_base_dir,_name)
	representation = get_representation_from_dir(dir_path)
	for r in representation:
		data={}
		data[r]=_name
		recorded_data.append(data)

def load_all_recorded(_dir):
	dirs = get_files_in_dir(_dir)
	for d in dirs:
		add_dir_representation_to_record(_dir,d)

def get_square_l2_distance(_representations,_r):
	min_distance =-1
	for r in _representations:
		d = r-_r
		sq_l2_d = np.dot(d,d)
		if min_distance<0 or min_distance>sq_l2_d:
			min_distance=sq_l2_d
	return min_distance

def get_closest_match(_dir):
	representation = get_representation_from_dir(_dir)
	closest_representation = {}
	closest_square_l2_distance = -1
	for r in recorded_data:
		r_val = r.iterkeys().next()
		sq_l2_distance= get_square_l2_distance(representations,r_val)
		if closest_square_l2_distance<0 or closest_square_l2_distance>sq_l2_distance:
			closest_square_l2_distance =sq_l2_distance
			closest_representation= r
	return closest_representation

def get_most_likely_name(_dir):
	r = get_closest_match(_dir)
	for k in r:
		return r[k]
	return 'unknown'

def learn_new_user(_dir,_base_dir,_name):
	dir_path =join(_base_dir,_name)
	os.mkdir(dir_path)
	files =get_files_in_dir(_dir)
	for f in files:
		shutil.copy(f,dir_path)
	add_dir_representation_to_record(_base_dir,_name)

def send_data_to_web_server(_response_type,_response_data):
	try:
		global data_channel
		data_channel.emit(_response_type,_response_data)
	except Exception as e:
		print_error(e)

class data_channel_namespace(BaseNamespace):

	def on_learn_user(self,*args):
		try:
			log_status("learning user : "+args[0]+' images at :'+args[1])
			learn_new_user(args[1],imgs_recorded_dir,_args[0])
			send_data_to_web_server('learned',args[0])
		except Exception as e:
			print_error(e)

	def on_get_user(self,*args):
		try:
			log_status("getting user for images at: "+args[0])
			user_name = get_most_likely_name(args[0])
			send_data_to_web_server('user_name',user_name)
		except Exception as e:
			print_error(e)

	def on_get_direct_forward_events(self,*args):
		while(True):
			try:
				direct_forward_events_to_web =['user_name']
				send_data_to_web_server('direct_forward_events_to_web',direct_forward_events_to_web)

				direct_forward_events_to_driver =['learn_user','get_user']
				send_data_to_web_server('direct_forward_events_to_driver',direct_forward_events_to_driver)
				break
			except Exception as e:
				print_error(e)

	def on_get_feature_name(self,*args):
		while(True):
			try:
				feature={'name':'face recog','info':'Performes face recognition'\
				,'web_path':'face_rcog'}
				send_data_to_web_server('set_feature_name',feature)
				break
			except Exception as e:
				print_error(e)

log_status('intializing...')
log_status('connecting web server...')
socketIO = SocketIO('localhost', 8080)
data_channel = socketIO.define(data_channel_namespace, '/automation_channel')
log_status('connected.')

def run_face_recog_loop(_refresh_time):
	while True:
		try:
			log_status("running running face recognition...")
		except Exception as e:
			print_error(e)
			pass
		time.sleep(_refresh_time)

def run_face_recog():
	load_all_recorded(imgs_recorded_dir)
	t1 = Thread(target=run_face_recog_loop, \
				args=(10000,))
	t1.start()
	socketIO.wait()
	t1.join()

run_face_recog()
