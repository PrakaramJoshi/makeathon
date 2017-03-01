import os
import os.path
import subprocess
from threading import Thread, Lock
# load datetime in the end
import datetime

def system_execute_get_stdout(_command):
	process = subprocess.Popen(_command, stdout=subprocess.PIPE, shell=True)
	while True:
		if process.poll() is not None:
			break
	return process.stdout.readlines()


def system_execute(_command):
	process = subprocess.Popen(_command, stdout=subprocess.PIPE, shell=True)
	return process

def create_directories(_directory):
	if not os.path.exists(_directory):
		os.makedirs(_directory)

mutex_datetime = Lock()

def get_datetime_format():
	return "%b-%d-%y %I:%M:%S%p"

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

all_process =[]

def launch_process(_service):
	command = _service['launcher']+" "+_service['application']
	process = system_execute(command)
	print 'started ',process.pid,' ',command
	global all_process
	all_process.append(process)

def kill_allprocess():
	for p in all_process:
		p.kill()
		print p.wait()


def get_services():
	cwd = os.getcwd()
	services =[ {'name':'ffmpeg','application':'-i /dev/video0 -r 1 images/a\%d.png','launcher':'/home/root/bin/ffmpeg/ffmpeg'}]
	return services


def run_scanner():
	cwd = os.getcwd()
	print os.getpid()
	services = get_services()
	for service in services:
		launch_process(service)
	while True:
		stop_all = raw_input("stop?")
		print stop_all
		if stop_all is'y' or stop_all is 'Y':
			kill_allprocess()
			break;

create_directories("images")
run_scanner()
