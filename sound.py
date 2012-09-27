#!/usr/bin/python
## This script takes input plots its waveform
## and plots a fft frquency plot
##

import alsaaudio, time, numpy, wave, scipy, sys, os
import matplotlib.pyplot as plot
import scipy.stats as stats
################################################################################
##Set up for alsaaudio
# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
################################################################################
def InitializeRecording(SampleRate):
  inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
  # Set attributes: Mono, 8000 Hz, 16 bit little endian samples
  inp.setchannels(1)
  inp.setrate(SampleRate)
  inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
  inp.setperiodsize(1024)
  return inp
################################################################################
##Set up for Wav output
def InitializeWave(SampleRate):
  w = wave.open('test.wav', 'w')
  w.setnchannels(1)
  w.setsampwidth(2)
  w.setframerate(SampleRate)
  return w

################################################################################
##this method gets the saved high and low output
def GetValidatedData():
  MagnitudeLow = numpy.load('MagnitudeLow.npy')
  MagnitudeHigh = numpy.load('MagnitudeHigh.npy')
  return MagnitudeLow, MagnitudeHigh

################################################################################
##this method compares the Sample with the validated data and returns a score
def ScoreSample(ValidatedTuple, Y):
  yLow, yHigh = ValidatedTuple
  LowScore = stats.ks_2samp(yLow, Y)[1]
  HighScore = stats.ks_2samp(yHigh, Y)[1]

  if LowScore > HighScore:
    return LowScore
  else:
    return HighScore

################################################################################
def CorrelateSample(ValidatedTuple, Y):
  yLow, yHigh = ValidatedTuple
  NormLow = yLow/yLow.max()
  NormHigh = yHigh/yHigh.max()
  NormY = Y/scipy.integrate.trapz(Y)
  LowScore  = numpy.correlate(NormY,NormLow).sum()
  HighScore = numpy.correlate(NormY,NormHigh).sum()

  if LowScore > HighScore:
    return LowScore
  else:
    return HighScore

################################################################################
def NormalDistribution(x,y):
  # picking 150 of from a normal distrubution
  # with mean 0 and standard deviation 1
  samp = scipy.norm.rvs(loc=0,scale=1,size=150)

  param = scipy.norm.fit(samp) # distribution fitting

  # now, param[0] and param[1] are the mean and
  # the standard deviation of the fitted distribution
  x = numpy.linspace(-5,5,100)
  # fitted distribution
  pdf_fitted = scipy.norm.pdf(x,loc=param[0],scale=param[1])
  # original distribution
  pdf = scipy.norm.pdf(x)

  plot.title('Normal distribution')
  plot.plot(x,pdf_fitted,'r-',x,pdf,'b-')
  plot.hist(samp,normed=1,alpha=.3)
  plot.show()

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
  while numpy.abs(Seconds -time.localtime()[5]) <= 1:
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

################################################################################
def GetFFT(Sample, SampleRate):
  #FFT Calculations
  Range = numpy.arange(len(Sample))
  FrequencyRange = Range*SampleRate/float(len(Sample)*numpy.pi)
  Frequency = scipy.fft(Sample)

  Magnitude = abs(Frequency)

 #Take the magnitude of fft of Sample and scale the fft so that it is not a function of the length
  Magnitude = Magnitude/float(len(Sample))

  #shits about to get real
  #Magnitude = Magnitude*Magnitude.conjugate()
  Magnitude= Magnitude**2
  return Magnitude, FrequencyRange

################################################################################
################################################################################
if __name__ == '__main__':
  SampleRate = 44100
  if len(sys.argv) == 2:
    if sys.argv[1] == '--sin-test':
      Sample = numpy.sin(5*2*numpy.pi*numpy.linspace(0,numpy.pi,SampleRate))
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

  ValidatedTuple = GetValidatedData()
  print Magnitude.shape
  Score = CorrelateSample(ValidatedTuple, Magnitude)
  print 'Score =', Score
  PlotSample(Sample, SampleRate, Magnitude, FrequencyRange)
