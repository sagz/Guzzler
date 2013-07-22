from StringIO import StringIO
import urllib2, os, sys, time

#MS Office
#url = "http://care.dlservice.microsoft.com/dl/download/2/9/C/29CC45EF-4CDA-4710-9FB3-1489786570A1/OfficeProfessionalPlus_x64_en-us.img"

#Chrome
url = 'https://dl.google.com/dl/linux/direct/google-chrome-unstable_current_x86_64.rpm'

#test
#url = "http://download.thinkbroadband.com/10MB.zip" # testing

time_bound = False
time_limit = 0
not_enough = True
rounds = 1000

if len(sys.argv)>1:
	if sys.argv[1][-1] == 's':
		try:
			time_bound = True
			time_limit = int(sys.argv[1][0:-1])
			print 'Guzzler started for %d seconds' % int(sys.argv[1][0:-1])
		except ValueError:
			pass
	elif sys.argv[1][-1] == 'm':
		try:
			time_bound = True
			time_limit = int(sys.argv[1][0:-1]) * 60
			print 'Guzzler started for %d minutes' % int(sys.argv[1][0:-1])
		except ValueError:
			pass
	elif sys.argv[1][-1] == 'h':
		try: 
			time_bound = True
			time_limit = int(sys.argv[1][0:-1]) * 60 * 60
			print 'Guzzler started for %d hours' % int(sys.argv[1][0:-1])
		except ValueError:
			pass
	else:
		try:
			if int(sys.argv[1])>0:
				rounds = int(sys.argv[1])
				print 'Guzzler started for %d rounds' % int(sys.argv[1])
		except ValueError:
			pass

file_name = url.split('/')[-1]
#guzzled_mb = 0.;
start_time = time.time()
semaphore = 0

while not_enough:
	u = urllib2.urlopen(url)
	#f = StringIO() #open(file_name, 'wb')
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	#print "Downloading: %s Bytes: %s" % (file_name, file_size)
	#guzzled_mb += 

	file_size_dl = 0
	block_sz = 1024*1
	while True:
	    buffer = u.read(block_sz)
	    if not buffer:
	        break

	    file_size_dl += len(buffer)
	    #f.write(buffer)
	    #status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
	    #status = status + chr(8)*(len(status)+1)
	    #print status,
	    current_guzzled = (semaphore*(float(file_size)/(1024*1024)))+(file_size_dl/(1024*1024))
	    elapsed_time = ((time.time()-start_time)/60)

	    guzzle_status = "\r%d mb guzzled in %.2f minutes with an average speed of %.2fMB/s." % (current_guzzled, elapsed_time, current_guzzled/elapsed_time/60)

	    print guzzle_status,

	    if time_bound:
	    	if time.time()-start_time > time_limit:
				#f.close()
				#os.remove(file_name)
				sys.exit(0)

	#f.close()

	# listing directories
	# print "The dir is: %s" %os.listdir(os.getcwd())

	# removing
	#os.remove(file_name)
	semaphore+=1

	if not time_bound:
		if semaphore >= rounds:
			not_enough = False #that is, enough is enough.