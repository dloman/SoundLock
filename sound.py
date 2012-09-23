#!/usr/bin/python
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm for sound capture. Set
## various attributes of the capture, and reads in a loop,
## Then prints the volume.
##
## To test it out, run it and shout at your microphone:

import alsaaudio, time, numpy, wave
 

################################################################################
##Set up for alsaaudio
# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
inp.setchannels(1)
inp.setrate(44100)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(1024)
################################################################################

################################################################################
##Set up for Wav output
w = wave.open('test.wav', 'w')
w.setnchannels(1)
w.setsampwidth(2)
w.setframerate(44100)
################################################################################

def PlotSample(Sample, SampleFreq):
  import matplotlib.pyplot as plot
  NumSamples = Sample.size
  TimeRange = numpy.arange(0, NumSamples, 1)
  print TimeRange
  TimeRange = (TimeRange / SampleFreq) * 1000 #divide by sample rate then scale to ms   
  print TimeRange
  plot.plot(TimeRange, Sample)
  plot.ylabel('Amplitude')
  plot.xlabel('Time(ms)')
  plot.show()

################################################################################
################################################################################
Seconds = time.localtime()[5]

while numpy.abs(Seconds -time.localtime()[5]) < 1:
  # Read data from device
  l,data = inp.read()
  if l:
    numbers = numpy.fromstring(data, dtype='int16')
    if 'Sample' in vars():
      Sample = numpy.append(Sample, numbers)
    else:
      Sample = numbers
    print 'numbers =',numbers.size
    w.writeframes(data)
print Sample.size
PlotSample(Sample,44100.0)	
