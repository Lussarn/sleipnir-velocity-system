import socket
import sys
import os
from subprocess import call

print "Sleipnir installation script for cameras"
print 

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

if os.getlogin() != "linus":
	print "You need to login as pi user and try again. Exiting."
	exit(0)


camera_number = ""
while camera_number != "1" and camera_number != "2":
	print "Which camera are you installing?"
	print "1 - Camera one (Left)"
	print "2 - Camera two (Right)"
	camera_number = raw_input("Enter camera number: ")
	if camera_number != "1" and camera_number != "2":
		print "Error: Please enter 1 for camera 1, or two for camera two"
		print	
camera_number = int(camera_number)

camera_ip = ""
print
while camera_ip == "":
	print "Please provide IP address of camera " + str(camera_number)
	camera_ip = raw_input("Enter camera " + str(camera_number) + " IP adress: ")
	try:
		socket.inet_aton(camera_ip)
	except socket.error:
		camera_ip = ""
		print "Error: Not a valid IP adress"
		print

camera1_ip = ""
if camera_number == 2:
	print
	while camera1_ip == "":
		print "Camera 2 syncs the clock with camera 1"
		print "Please provide IP address of camera 1"
		camera1_ip = raw_input("Enter camera 1 IP adress: ")
		try:
			socket.inet_aton(camera1_ip)
		except socket.error:
			camera1_ip = ""
			print "Error: Not a valid IP adress"
			print

base_ip = ""
print
while base_ip == "":
	print "Please provide IP address of base station"
	base_ip = raw_input("Enter base station IP adress: ")
	try:
		socket.inet_aton(base_ip)
	except socket.error:
		base_ip = ""
		print "Error: Not a valid IP adress"
		print

print
print "Ok, we have all required info"
print "Camera number: " + str(camera_number)
print "Camera ip: " + camera_ip
if camera_number == 2:
	print "Camera 1 ip: " + camera1_ip
print "Base station ip: " + base_ip
print
print "Is the above info correct?"
print 'Enter "yes" to write config files'
confirm = raw_input(": ")
if confirm != "yes":
	print "Aborting..."
	print
	sys.exit(1)

def copy_file_with_substitutions(infile, outfile, substitutions):
	print "copying " + infile + " to " + outfile
	try:
		with file(infile) as f:
			content = f.read()
	except:
		print "Unable to read file: " + infile
		return False

	print content

def userland():
	print "Downloading userland..."
	status = os.system("/Users/linus/homebrew/bin/wget -O /tmp/userland.zip https://github.com/raspberrypi/userland/archive/master.zip")
	if status != 0:
		print "Error: Unable to download latest userland zip. Exiting."
		exit(1)
	print "Unzipping userland..."
	status = os.system("/usr/bin/unzip -q -o ~/userland.zip -d ~/")
	if status != 0:
		print "Error: Unable to unzip userland zip. Exiting."
		exit(1)

	try:
		os.chdir("~/userland-master")
		os.system("./buildme")
	except:
		print "Unable to build userland. Exiting."
		exit(1)

def apt():
	print "Installing dependacies..."
	status = os.system("apt-get --force-yes install git-core gcc build-essential cmake libb64-dev libcurl4-openssl-dev libturbojpeg1-dev")

	
userland()	

exit(0)

print "building sleipnir..."
os.chdir("sleipnir")
status = os.system.call("./build")
exit(0)
print
print "Configuring ntp.conf"
ntp_filename = "./extra-files/ntp.conf.v" + str(camera_number)
copy_file_with_substitutions(ntp_filename, "/Users/linus/etc/ntp.conf", { "CAMERA1_IP_ADDRESS", camera1_ip })


