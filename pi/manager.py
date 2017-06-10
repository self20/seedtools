#!/usr/bin/python
import redis
import os
import json
import subprocess

r = redis.StrictRedis(host='localhost', port=6379, db=0)
credential = os.environ['credential']
seedboxIp = os.environ['seedip']
print(credential)
print(seedboxIp)

def register(processId):
	r.set('process', processId)
		
def unregister():
	r.delete('process')
	
def isProcessAvailable():
	isAlreadyRunning =not r.get('process') 
	print isAlreadyRunning
	return isAlreadyRunning
	
def download(fileName):
	print(filename)

def clear():
	r.delete('process')
	r.delete('files')
	
def callExternalShell(command):
	print command
	subprocess.call(command, shell=True)
	
def listFiles():
	files = []	
	if r.get('files'):
		files = json.loads(r.get('files'))
	print(files)
	#list files on remote 
	proc = subprocess.Popen(['ssh', 'root@'+seedboxIp, 'ls', '/home/rtorrent/sync/'], stdout=subprocess.PIPE)
	for newfileName in proc.stdout.readlines():
		file = { 'state' : 'waiting', 'name' : newfileName}
		if (any(x['name'] == newfileName for x in files)):
			print("already in redis : " + newfileName)
		else :
			files.append(file);
	r.set('files',json.dumps(files))

def syncStart():
	if r.get('files'):
		files = json.loads(r.get('files'))
		for file in files:
			if file['state'] == 'waiting':
				callExternalShell("touch "+seedboxIp+"/dl..."+file['name'])
				file['state'] = 'downloading'
				#updating redis
				r.set('files',json.dumps(files))
				#start downloading
				callExternalShell("wget -r --no-passive --no-parent  ftp://"+credential+"@"+seedboxIp+"/"+file['name'])
				callExternalShell("rm "+seedboxIp+"/dl..."+file['name'])

clear()		
processId = os.getpid()
print('launching process Id : '  + str(processId))
if isProcessAvailable() : 
	register(processId)
	#link to ssh conf
	callExternalShell(". ~/.keychain/raspberrypi-sh")
	#normalize files on seedbox
	callExternalShell("ssh root@"+seedboxIp+" /root/seedtools/seedbox/normalize.py")
	#list remote files
	listFiles()
	syncStart()
	#unregister
	unregister()
else :
	#do nothing
	print("max process is reached")