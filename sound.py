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
def floor(Input, Scale):
  return numpy.floor(Input/Scale)*Scale

################################################################################
##this method compares the Sample with the validated data and returns a score
def ScoreSample(ValidatedTuple, Y,x):
  yLow, yHigh = ValidatedTuple

  #Floor zeros to avoid amplification of low signal
  yLow  = floor(yLow, 10)
  yHigh = floor(yHigh, 10)
  Y     = floor(Y, 10)
  
  yLow = (yLow/numpy.trapz(yLow)); yHigh = (yHigh/numpy.trapz(yHigh))
  Y = (Y/numpy.trapz(Y))
  #Trim edges and multiply source, scale factor and validated data 
  HighScore = yHigh[200:-200]* Y[200:-200] *100000
  LowScore  = yLow[200:-200] * Y[200:-200] *100000
  print len(HighScore),len(LowScore)
  print len(HighScore),len(LowScore)
  plot.plot(x[200:-200],LowScore, 'r')
  plot.plot(x[200:-200],HighScore, 'b')

  HighScore = floor(HighScore, .1)
  LowScore  = floor(LowScore, .1)
  plot.show()
  HighScore = numpy.trapz(HighScore)
  LowScore  = numpy.trapz(LowScore)
  if LowScore > HighScore:
    return LowScore
  else:
    return HighScore

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
  switch = True
  while switch ==True:
    # Read data from device
    l,data = inp.read()
    if l:
      numbers = numpy.fromstring(data, dtype='int16')
      if 'Sample' not in vars():
        Sample = numbers
      else:
        Sample = numpy.append(Sample, numbers)
        if len(Sample) > 20000:
          HalfPoint = len(Sample/2)
          Sample = Sample[HalfPoint-20000:HalfPoint+20000]
          return Sample
          w.writeframes(data)
  
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
  numpy.save('Output', Magnitude)

  ValidatedTuple = GetValidatedData()
  Score = ScoreSample(ValidatedTuple, Magnitude,FrequencyRange)
  print 'Score =', Score
  PlotSample(Sample, SampleRate, Magnitude, FrequencyRange)
