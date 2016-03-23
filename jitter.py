import os
import sys

image = 1
filename = "/home/linus/rctest/3/" +sys.argv[1]+ "/timestamps.txt" 

tt = {}
with open(filename) as f:
	content = f.readlines()
for data in content:
	data = data.split()
	if len(data) == 2:
		tt[int(data[0])] = int(data[1])

minjitter = 1000000
maxjitter = 0
last = 0

j = {}
for i in xrange(0,1000):
	j[i] = 0
while True:
	if image % 10000 == 0:
		print image, minjitter, maxjitter

	if not image in tt:
		break;
	timestamp = tt[image];
	if timestamp == 0:
		break

	if last == 0:
		last = timestamp
		continue

	jitter = timestamp - last
 	if jitter < 0:
 		print image, jitter
		break

	if (jitter < minjitter and image > 500):
		minjitter = jitter

	if (jitter > maxjitter and image > 500):
 		maxjitter = jitter

	j[jitter] += 1

	last = timestamp
	image += 1

print "image: ",image
print "minjitter: ", minjitter
print "maxjitter: ", maxjitter
print
t = 0.0
for i in xrange(minjitter, maxjitter + 1):
	print i,j[i]
	t += i * j[i]

print str(image / t * 1000) + "fps"
