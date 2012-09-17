import time, sys
import pymedia.audio.sound as sound
import pymedia.audio.acodec as acodec

from scipy import *
import wave

# takes sound in Hz and returns a string with the name of the closest note
def find_closest_note(sound):
    dist = 99999
    result = ""
    for i in notes.keys():
        newDist = abs(sound-i)
        if newDist<dist:
            dist = newDist
            result = notes[i]
    return result

notes = dict({
55:"(LOW)",
65.41:"C2",
69.3:"C#2",
73.42:"D2",
77.78:"D#2",
82.41:"E2",
87.31:"F2",
92.5:"F#2",
98:"G2",
103.83:"G#2",
110:"A2",
116.54:"A#2",
123.47:"B2",
130.81:"C3",
138.59:"C#3",
146.83:"D3",
155.56:"D#3",
164.81:"E3",
174.61:"F3",
185:"F#3",
196:"G3",
207.65:"G#3",
220:"A3",
233.08:"A#3",
246.94:"B3",
261.63:"C4",
277.18:"C#4",
293.66:"D4",
311.13:"D#4",
329.63:"E4",
349.23:"F4",
369.99:"F#4",
392:"G4",
415.3:"G#4",
440:"A4",
466.16:"A#4",
493.88:"B4",
523.25:"C5",
554.37:"C#5",
587.33:"D5",
622.25:"D#5",
659.26:"E5",
698.46:"F5",
739.99:"F#5",
783.99:"G5",
830.61:"G#5",
880:"A5",
932.33:"A#5",
987.77:"B5",
1046.5:"C6",
1108.7:"C#6",
1174.7:"D6",
1244.5:"D#6",
1318.5:"E6",
1400:"(HIGH)"
})

time_to_record = 20 # seconds. also read from input. only relevant if from_mic=True
sample_rate = 44100 # samples per second
FACTOR = 1.0
number_of_samples_to_process = int(8192*FACTOR) # 2^14 to make FFT work fast, and enough time for accurate reading, but not too long so we don't have too much spread
snd = 0
from_mic = True # if True, the prog takes input from mic. if False - from file named filename
file_is_over = False # set to True when input file is over.
filename = "../chords/yonatan hakatan.wav"
peaks_only = True #
cur_time = 0.0
cur_sample = 0
now_playing = dict()
sound_vector = []
last_processed_time = 0.8 # seconds
interval = 0.025 # seconds
sound_events = [] # will contain ( time , event_number: 1=start, 2=stop , note_index , note_name )

DecaySamplesNeeded = 3 # this is how many samples in a row are needed to find a decay
DecayFactor = 0.98 # how strong should decay be in order to be detected (low = strong decay. 1 = every decay is detected)
ReplayFactor = 0.75 # how strong should re-play be to be detected. 1 = very weak is detected. 0.5 - medium. 0.1 - only very aggressive re-play is detected

MinPower = 1500000*FACTOR # minimum power to detect note
StopAreaPower = 1200000*FACTOR # power below which notes have to go to be stopped
DetectionFrames = 1 # how many frames should we wait before we put detected notes in the events vector. "waits" to see if this is a real tone or an overtone
StopPower = 80000*FACTOR*2

def init():
    global snd
    if(from_mic):
        snd = sound.Input( sample_rate, 1, sound.AFMT_S16_LE )
    else:
        snd = wave.open(filename)
       
def start_rec():
    if(from_mic):
        snd.start()
       
def read_data():
    global cur_sample
    global cur_time
    global sound_vector
   
    if(from_mic):
        temp = snd.getData()
    else:
        temp = snd.readframes( 1000 )
        if(len(temp)==0):
            global file_is_over
            file_is_over = True
   
    if temp and len( temp ):
        for i in range(0, len(temp), 2):
            t = ord(temp[i])+256*ord(temp[i+1])
            if t > 32768:
                t = -65536 + t
            sound_vector.append(t)
            cur_sample += 1
        cur_time = double(cur_sample)/sample_rate
    else: # this is only needed in microphone mode. i'm not sure it will be needed when we integrate with the game...
      time.sleep( .003 )

def is_finished():
    if(from_mic):
        return (not(snd.getPosition() <= time_to_record))
    else:
        return file_is_over

def stop_rec():
    if(from_mic):
        snd.stop()
    else:
        snd.close()
       
def voiceRecorder(  ):
    global sound_events

    init()

    start_rec()

    # Loop until recorded position greater than the limit specified
    while (not(is_finished())):
        read_data()
        analyse_sound()
        for i in sound_events:
            ( time , event_type , note_index , note_name ) = i
            print "%.2f\t%d\t%d\t%s\t%f" % (time , event_type , note_index , note_name,float(note_index)*sample_rate/number_of_samples_to_process)
        sound_events = []
   
    # Stop listening the incoming sound from the microphone or line in
    stop_rec()

 
def analyse_sound():
    # if we processed just a short while ago, no need to run again. return.
    if (cur_time < last_processed_time + interval):
        return
    global last_processed_time
    last_processed_time = cur_time
    global sound_vector
    global sound_events
    sound_vector = sound_vector[-number_of_samples_to_process:]
    N=len(sound_vector)
    #print N
    S=abs(fft(sound_vector))
    #print len(S)
    f=sample_rate*r_[0:(N/2)]/N
    n=len(f)
    S = S[0:n];
    S[0:1] = 0

    # BEWARE - UGLY PATCH AHEAD
    # this line removes energy from the noisy 50Hz/100Hz band
    #S[74]=0
    #S[37]=0
    #S[19]=0
    #S[18]=0

    if(peaks_only):
       
        # BEWARE - UGLY PATCH AHEAD
        # the following lines remove overtones of detected notes.
        for j0 in now_playing.keys():
            S[floor(2*j0/1.029):ceil(2*j0*1.029)] = 0
            S[floor(3*j0/1.029):ceil(3*j0*1.029)] = 0
            S[floor(4*j0/1.029):ceil(4*j0*1.029)] = 0
            S[floor(5*j0/1.029):ceil(5*j0*1.029)] = 0

        # delete from the FFT all sounds that we already know that are playing,
        # and check if they stopped playing
        for j0 in now_playing.keys():
            # read parameters from last sample
            (time, last_power, max_power, last_area_power, max_area_power, was_decaying, detected_frames) = now_playing[j0]
            v0 = double(j0)*sample_rate/N
            # get current sample parameters
            curr_power = S[j0]
            curr_area_power = sum(S[floor(j0/1.029):ceil(j0*1.029)])

            if(curr_power > MinPower):
                detected_frames += 1

            if( detected_frames == DetectionFrames ):
                #sound_events.append((time, 1, j0, find_closest_note(v0)))
                #print "%d: %s (%d) started playing at volume %d"  % (cur_sample, find_closest_note(v0),j0,curr_area_power)
                detected_frames += 1
                               
            # keep track of maximum power
            if(curr_power > max_power):
                max_power = curr_power

            # keep track of maximum power
            if(curr_area_power > max_area_power):
                max_area_power = curr_area_power

            # check if power is dropping
            if(curr_power < last_power * DecayFactor):
                was_decaying += 1

            # if power is going up, and we have already seen it dropping - the sounds must have been played again.
            if((curr_power*ReplayFactor > last_power)and(was_decaying >= DecaySamplesNeeded)):
                was_decaying = 0
                nn = find_closest_note(v0)
                if(detected_frames >= DetectionFrames):
                    sound_events.append((cur_time, 2, j0, nn))
                    sound_events.append((cur_time, 1, j0, nn))
                    print "%d: \t%s (%d) re-started playing" % (cur_sample, nn,j0)
                #print "%.2f: %s (%d) started playing" % (cur_time, nn,j0)

            # update all parameters in our dict
            now_playing[j0] = (time, curr_power, max_power, last_area_power, max_area_power, was_decaying, detected_frames )

            # remove power from the sonogram
            S[floor(j0/1.029):ceil(j0*1.029)] = 0

            # check if note stopped = droped to 0.3 of maximum power
            #if ((curr_area_power < max_area_power * 0.25)):
            #if (curr_area_power < StopAreaPower):
            if(curr_power < StopPower):
                now_playing.pop(j0)
                #if(detected_frames >= DetectionFrames):
                sound_events.append((cur_time, 2, j0, find_closest_note(v0)))
                print "%.2f: \t%s (%d) stopped playing at volume %d" % (cur_time, find_closest_note(j0*sample_rate/N),j0,curr_power)
            #if(j0==110):
            #    print "\t%.2f %d %d %d %d %d " % (cur_time, curr_power, max_power, curr_area_power, max_area_power,was_decaying)
           
           
        # now look for new notes that are strong enough to be considered as playing
        flag=True
        while(flag):
            j0 = S.argmax(None)
            i0 = S[j0]
            v0 = double(j0)*sample_rate/N
            if((i0>MinPower) and (v0>70) and (abs(v0-100)>1)):
                t = sum(S[floor(j0/1.029):ceil(j0*1.029)])
                now_playing[j0] = (cur_time, i0,i0, t, t, 0, 0 )
                print "%d: %s (%d) started playing at volume %d"  % (cur_sample, find_closest_note(v0),j0,t)
                sound_events.append((cur_time, 1, j0, find_closest_note(v0)))
               
                flag = False
            if(i0<=MinPower):
                flag = False
            S[floor(j0/1.029):ceil(j0*1.029)] = 0
        #j1 = S.argmax(None)
        #i1 = S[j1]
        #v1 = double(j1)*sample_rate/N
        #S[j1-5:j1+5] = 0
        #print "%.2f\t%.2f\t%.2f\t%s\t%.1f\t%.2f\t%s\t%.1f" % (cur_time, double(cur_time)/sample_rate, v0, find_closest_note(v0),i0,v1, find_closest_note(v1),i1)
       
    else: # not peaks_only - create full sonogram. mostly to export to matlab for research
        out = []
        St = ""
        for i in S:
            i = i/100
            St+="%d," % i
        print St

# ----------------------------------------------------------------------------------

if __name__ == "__main__":
  if(len(sys.argv)==1):
      print "\n\n\nusage: "
      print "to record from microphone:    %s <time to record in seconds>" % sys.argv[0]
      print "to read from file:            %s -f filename" % sys.argv[0]
      print "add \"-full\" to analyse full histogram\n\n\n"
      sys.exit(0)
  try:
      time_to_record = int(sys.argv[1])
  except Exception,e:
      pass
  for i in range(0, len(sys.argv) ):
      if sys.argv[i]=="-f":
          filename = sys.argv[i+1]
          from_mic = False
      if sys.argv[i]=="-full":
          peaks_only = False
 
  voiceRecorder(  )
