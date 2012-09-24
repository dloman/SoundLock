#!/usr/bin/python
## This script takes input plots its waveform
## and plots a fft frquency plot
##

import alsaaudio, time, numpy, wave, scipy, sys
import matplotlib.pyplot as plot
import scipy.stats as stats
################################################################################
##Set up for alsaaudio
# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
def InitializeRecording(SampleRate):
  inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
  # Set attributes: Mono, 8000 Hz, 16 bit little endian samples
  inp.setchannels(1)
  inp.setrate(SampleRate)
  inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
  inp.setperiodsize(1024)
  return inp
################################################################################

################################################################################
##Set up for Wav output
def InitializeWave(SampleRate):
  w = wave.open('test.wav', 'w')
  w.setnchannels(1)
  w.setsampwidth(2)
  w.setframerate(SampleRate)
  return w

################################################################################
def PlotSample(Sample, SampleFreq, Magnitude, FrequencyRange):
  NumSamples = Sample.size
  TimeRange = numpy.arange(0, NumSamples, 1)
  TimeRange = (TimeRange / float(SampleFreq)) * 1000 #divide by sample rate then scale to ms
  print TimeRange
  #plot time phase space
  plot.subplot(2,1,1)
  plot.plot(TimeRange, Sample)
  plot.ylabel('Amplitude')
  plot.xlabel('Time(ms)')
  #plot frequency phase space
  plot.subplot(2,1,2)
  plot.plot(FrequencyRange, Magnitude)
  plot.xlabel('Frequency(Hz)')
  plot.ylabel('Amplitude')
  plot.show()


################################################################################
def GetSample(SampleRate):
  inp = InitializeRecording(SampleRate)
  w = InitializeWave(SampleRate)
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
  #PlotSample(Sample,SampleRate)
  return Sample

def GetFFT(Sample, SampleRate):
  #FFT Calculations
  Range = numpy.arange(len(Sample))
  FrequencyRange = Range*SampleRate/(len(Sample)*10.0)
  Frequency = scipy.fft(Sample)

  Magnitude = abs(Frequency)

 #Take the magnitude of fft of Sample and scale the fft so that it is not a function of the length
  Magnitude = Magnitude/float(len(Sample))

  #shits about to get real
  Magnitude = Magnitude**2
  return Magnitude, FrequencyRange

################################################################################
################################################################################
if __name__ == '__main__':
  SampleRate = 44100
  if len(sys.argv) == 2:
    if sys.argv[1] == '--sin-test':
      Sample = numpy.sin(5*numpy.linspace(0,3.14))
    else:
      print '----------------------------------------------------------------------------------'
      print "sound.py--This program takes input from microphone and plots it's waveform"
      print "it then takes that waveform tranforms it into frequency space and plots the output"
      print '----------------------------------------------------------------------------------'
      print '\nUsage $./sound.py [--sin-test] \n'
      print 'Default takes input from microphone plots --sin-test runs funtion using a sinwave\n'
      exit()
  else:
    Sample = GetSample(SampleRate)
  Magnitude, FrequencyRange = GetFFT(Sample, SampleRate)
  DataFirstHalf = numpy.array([FrequencyRange[0:len(FrequencyRange)/2.0], Magnitude[0:len(Magnitude)/2.0]])
  DataSecondHalf = numpy.array([FrequencyRange[len(FrequencyRange)/2.0:-1], Magnitude[len(Magnitude)/2.0:-1]])
  Gaussian = stats.norm
  Peak1, StandardDev1 = Gaussian.fit(DataFirstHalf)
  Peak2, StandardDev2 = Gaussian.fit(DataSecondHalf)
  print 'Peak1 =',Peak1,'StandardDeviation1 =',StandardDev1
  print 'Peak2 =',Peak2,'StandardDeviation2 =',StandardDev2
  PlotSample(Sample, SampleRate, Magnitude, FrequencyRange)
