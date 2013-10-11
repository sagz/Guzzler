Guzzler
==
Guzzler is a tool to test a networks true download bandwidth.
Many ISPs provide burst download speeds which give them good results on speedtest.net but won't actually convert to a better browsing experience.
Guzzler guzzles network bandwidth to let you know the true download bandwidth over time.

Usage    
==
`$ python3 downloader.py --help`

```
usage: downloader.py [-h]
                     [-s SECONDS | -m MINUTES | -hr HOURS | -d DAYS | -mb MEGABYTES | -gb GIGABYTES | -tb TERABYTES]

Guzzle Away! Guzzler is a tool that will guzzle your internet bandwidth. It
does this by downloading packages from many high-speed servers and discarding
them instantly. This is helpful if you want to know the true sustainable
bancwidth of your internet.

optional arguments:
  -h, --help            
    show this help message and exit
  
  -s SECONDS, --seconds SECONDS
    Number of seconds to guzzle away. Default is 1000 years.
  
  -m MINUTES, --minutes MINUTES
    Number of minutes to guzzle away. Default is 1000 years.
  
  -hr HOURS, --hours HOURS
    Number of hours to guzzle away. Default is 1000 years.
  
  -d DAYS, --days DAYS
    Number of days to guzzle away. Default is 1000 years.
  
  -mb MEGABYTES, --megabytes MEGABYTES
    Number of megabytes to download. Default is time-bound to run 1000 years.
  
  -gb GIGABYTES, --gigabytes GIGABYTES
    Number of gigabytes to download. Default is time-bound to run 1000 years.
  
  -tb TERABYTES, --terabytes TERABYTES
    Number of terabytes to download. Default is time-bound to run 1000 years.
```

Features
==
+ Multi Threaded
+ ANSI Colour output!
+ Lightweight
+ **requires** Python 3
 
To - Do
==
Non python, browser-based version?  
[Implement 'background' mode](http://stackoverflow.com/questions/17983355/detect-if-network-is-idle-in-python)
