#!/usr/bin/env python2
# Closed-loop image presentation with encoder on wheel

from psychopy import visual, event, core, monitors, logging, tools, filters
from pvapi import PvAPI, Camera
import time
from scipy.misc import imsave
import numpy as np
import multiprocessing as mp
import threading
from Queue import Queue
import sys
import errno
import os
import optparse

import pylab, math, serial, numpy

import random
import itertools
import cPickle as pkl

from datetime import datetime
import re
import StringIO
import scipy.misc

from libtiff import TIFF
import random
import string

from serial import Serial
from PIL import Image, ImageSequence

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split('(\d+)', text) ]

# RUN IN CMD LINE TO TURN AVI INTO FRAMES:
# ffmpeg -i natural_movie.avi -vcodec png -ss 10 -vframes 1 -an -f rawvideo test.png

# # OR THIS WORKS:
# v_fps = 60 #0.08 # -r :n frames to extract per second
# movie = 'natural_movie.avi' # -i : read from input files, and write to outputfiles
# v_fmt = 'image2' # 'image2' # -f : format of input 
# # v_size = '128x96'
# # v_opts = "-i %s -r %s -f %s -s %s" % (movie, str(v_fps), v_fmt, v_size)
# v_opts = "-i %s -r %s -f %s" % (movie, str(v_fps), v_fmt)
# os.system("ffmpeg "+ v_opts + " ./test/%4d.png")
# # os.system("ffmpeg -i natural_movie.avi -r 0.08 -f image2 -s 128x96 %4d.png")

ser = Serial('/dev/ttyACM3', 115200, timeout=2) # Establish the connection on a specific port
def flushBuffer():
    #Flush out Teensy's serial buffer
    tmp=0;
    while tmp is not '':
        tmp=ser.readline()


monitor_list = monitors.getAllMonitors()

parser = optparse.OptionParser()
parser.add_option('--no-camera', action="store_false", dest="acquire_images", default=True, help="just run PsychoPy protocol")
parser.add_option('--save-images', action="store_true", dest="save_images", default=False, help="save camera frames to disk")
parser.add_option('--output-path', action="store", dest="output_path", default="/tmp/frames", help="out path directory [default: /tmp/frames]")
parser.add_option('--output-format', action="store", dest="output_format", type="choice", choices=['tif', 'png', 'npz', 'pkl'], default='tif', help="out file format, tif | png | npz | pkl [default: tif]")
parser.add_option('--use-pvapi', action="store_true", dest="use_pvapi", default=True, help="use the pvapi")
parser.add_option('--use-opencv', action="store_false", dest="use_pvapi", help="use some other camera")
parser.add_option('--fullscreen', action="store_true", dest="fullscreen", default=True, help="display full screen [defaut: True]")
parser.add_option('--debug-window', action="store_false", dest="fullscreen", help="don't display full screen, debug mode")
parser.add_option('--write-process', action="store_true", dest="save_in_separate_process", default=True, help="spawn process for disk-writer [default: True]")
parser.add_option('--write-thread', action="store_false", dest="save_in_separate_process", help="spawn threads for disk-writer")
parser.add_option('--monitor', action="store", dest="whichMonitor", default="testMonitor", help=str(monitor_list))

parser.add_option('--make_frames', action="store_true", dest="make_frames", default=False, help="make frames from movie? T/F")
parser.add_option('--source-file', action="store", dest="source_file", default="", help="source file (.avi) for movie if making frames")

(options, args) = parser.parse_args()

#acquisition options:
use_pvapi = options.use_pvapi

# acquisition save options:
acquire_images = options.acquire_images
save_images = options.save_images
if not acquire_images:
    save_images = False
output_path = options.output_path
output_format = options.output_format
save_in_separate_process = options.save_in_separate_process

save_as_tif = False
save_as_png = False
save_as_npz = False
save_as_dict = False
if output_format == 'png':
    save_as_png = True
elif output_format == 'tif':
    save_as_tif = True
elif output_format == 'npz':
    save_as_npz = True
else:
    save_as_dict = True

# stimulus display options
fullscreen = options.fullscreen
whichMonitor = options.whichMonitor
if not fullscreen:
    winsize = [800, 600]
else:
    winsize = monitors.Monitor(whichMonitor).getSizePix()

print "Window size:  ", winsize
print "Ouput format: ", output_format

# stimulus options:
make_frames = options.make_frames
source_file = options.source_file


# Make the output path if it doesn't already exist
try:
    os.mkdir(output_path)
except OSError, e:
    if e.errno != errno.EEXIST:
        raise e
    pass

# Make the info path if it doesn't already exist
# soft code rel to output-path
info_path = output_path + '/frame_info'
try:
    os.mkdir(info_path)
except OSError, e:
    if e.errno != errno.EEXIST:
        raise e
    pass




# -------------------------------------------------------------
# Camera Setup
# -------------------------------------------------------------

camera = None

if acquire_images:

    print('Searching for camera...')

    # try PvAPI
    if use_pvapi:

        pvapi_retries = 50

        try:
            camera_driver = PvAPI(libpath='./')
            cameras = camera_driver.camera_list()
            cam_info = cameras[0]

            # Let it have a few tries in case the camera is waking up
            n = 0
            while cam_info.UniqueId == 0L and n < pvapi_retries:
                cameras = camera_driver.camera_list()
                cam_info = cameras[0]
                n += 1
                time.sleep(0.1)

            if cameras[0].UniqueId == 0L:
                raise Exception('No cameras found')
            camera = Camera(camera_driver, cameras[0])

            print("Bound to PvAPI camera (name: %s, uid: %s)" % (camera.name, camera.uid))

        except Exception as e:

            print("Unable to find PvAPI camera: %s" % e)

    if camera is None:
        try:
            import opencv_fallback

            camera = opencv_fallback.Camera(0)

            print("Bound to OpenCV fallback camera.")
        except Exception as e2:
            print("Could not load OpenCV fallback camera")
            print e2
            exit()


# -------------------------------------------------------------
# Set up a thread to write stuff to disk
# -------------------------------------------------------------

if save_in_separate_process:
    im_queue = mp.Queue()
else:
    im_queue = Queue()

disk_writer_alive = True


def save_images_to_disk():
    print('Disk-saving thread active...')

    n = 0

    currdict = im_queue.get() # get the dict 

    # Make the output path if it doesn't already exist
    curr_impath = '%s/%s/' % (output_path, currdict['condName'])
    curr_infopath = '%s/%s/' % (info_path, currdict['condName'])
    if not os.path.exists(curr_impath):
        os.mkdir(curr_impath)

    if not os.path.exists(curr_infopath):
        os.mkdir(curr_infopath)

    header = ''
    placeholder = ''
    for k in currdict.keys():
        header = header + k + '\t '
        placeholder = placeholder + '%s\t '

    # Initiate txt file to write exp. params:
    frame_info = open(curr_infopath + 'frame_info.txt', 'w')
    # frameTimeOutputFile.write('frameCount\t n\t frameCond\t frameT\t interval\n')
    frame_info.write(header)
    
    while currdict is not None:

        # frame_info.write('%i\t %i\t %i\t %s\t %s\n' % (int(currdict['frame']),n,int(currdict['cond']),currdict['time'],currdict['interval']))
        frame_info.write(placeholder % (str(currdict[i]) for i in currdict.keys()))

        if save_as_png:
            fname = '%s/%s/%i_%i_%i_SZ%s_SF%s_TF%s_pos%s_cyc%s_stim%s.png' % (output_path, currdict['condName'], int(currdict['time']), int(currdict['frame']), int(n), str(currdict['size']), str(currdict['sf']), str(currdict['tf']), str(currdict['pos']), str(currdict['cycleidx']), str(currdict['stim']))
            # tiff = TIFF.open(fname, mode='w')
            # tiff.write_image(currdict['im'])
            # tiff.close()

        elif save_as_tif:
            fname = '%s/%s/t%i_mov%i_cam%i.tif' % (output_path, currdict['condName'], int(currdict['time']), int(currdict['frame']), int(n))
            tiff.write_image(currdict['im'])
            tiff.close()

        elif save_as_npz:
            np.savez_compressed('%s/test%d.npz' % (output_path, n), currdict['im'])
        
        else: # save as full dict...

            fname = '%s/%s/00%i_%i_%i_%i.pkl' % (output_path, currdict['condName'], int(currdict['condNum']), int(currdict['time']), int(currdict['frame']), int(n))
            with open(fname, 'wb') as f:
                pkl.dump(currdict, f, protocol=pkl.HIGHEST_PROTOCOL) #protocol=pkl.HIGHEST_PROTOCOL)
        #if n % 100 == 0:
        #print 'DONE SAVING FRAME: ', currdict['frame'], n #fdict
        n += 1
        currdict = im_queue.get()

    disk_writer_alive = False
    print('Disk-saving thread inactive...')


if save_in_separate_process:
    disk_writer = mp.Process(target=save_images_to_disk)
else:
    disk_writer = threading.Thread(target=save_images_to_disk)

if save_images:
    disk_writer.daemon = True
    disk_writer.start()

# Formatting for saving:
FORMAT = '%Y%m%d%H%M%S%f'
allow = string.letters + string.digits + '-'


# -------------------------------------------------------------
# Stimulus Presentation
# -------------------------------------------------------------

# --MAKE PRES WINDOW--
from psychopy.tools import imagetools
background_color = (-1, -1, -1)
# win = visual.Window(fullscr=fullscreen, size=winsize, units='pix', monitor=whichMonitor, color = (0,0,0))
win = visual.Window(fullscr=fullscreen, size=winsize, units='deg', monitor=whichMonitor, color = background_color)

globalClock = core.Clock()


stim_dir ='./stimuli/test/'

# --CREATE MOVIE FRAMES IF NEED TO--
if make_frames is True:
    v_fps = 60 #0.08 # -r :n frames to extract per second
    # movie = source_dir + 'natural_movie.avi' # -i : read from input files, and write to outputfiles
    movie = source_file
    v_fmt = 'image2' # 'image2' # -f : format of input 
    # v_size = '128x96'
    # v_opts = "-i %s -r %s -f %s -s %s" % (movie, str(v_fps), v_fmt, v_size)
    v_opts = "-i %s -r %s -f %s" % (movie, str(v_fps), v_fmt)
    os.system("ffmpeg "+ v_opts + " " + stimdir + "/%4d.png")
    # os.system("ffmpeg -i natural_movie.avi -r 0.08 -f image2 -s 128x96 %4d.png")


# --GET FILENAMES OF ALL THE STIMULI--

imlist=sorted((fn for fn in os.listdir(stim_dir) if fn.endswith('.png')), key=natural_keys)
stim_nframes = len(imlist)

# --LOAD STIMULI--
print "Loading stimuli..."
frame_array=[]
for fn in range(len(imlist)):
    fname = stim_dir+imlist[fn]
    fframe = Image.open(fname)
    frame_array.append(visual.ImageStim(win, image=fframe))

print("ALL IMAGES LOADED!")


# --EXP LAYOUT--
conds = [0, 1]
labels = ['blank', 'natural']
cond_labels = [labels[int(s)] for s in conds]



# --TIMING PARAMS--
frame_counter = 0 # n frames acquried by camera
n_refresh = 0 # n monitor refreshes
report_period = 60 # frames
t = 0
last_t = None

nframes = 0


if acquire_images:
    # Start acquiring
    win.flip()
    time.sleep(0.002)
    camera.capture_start()
    camera.queue_frame()
        


#To Break Out of Loop
class BreakIt(Exception): pass


# --DO IT--

curr_cond = 1

import pdb
pdb.set_trace()

try:

    win.flip() # first clear everything
    time.sleep(1) # wait a sec

    t_expt_start = globalClock.getTime()

    while True:
        t = globalClock.getTime()

        # Show frame:
        # SHOW MIDDLE FRAME instead??
        frame_array[n_refresh].draw()

        win.flip()
        t_flip = globalClock.getTime()

        # Get locomotion info:
        curr_mvmt = []
        print "FLIP!"
        while (globalClock.getTime() - t_flip <= 1/60.):
            # print globalClock.getTime() - t_flip
            curr_mvmt.append(ser.readline().strip())

        # print curr_mvmt
        curr_mvmt = [float(i) for i in curr_mvmt if not i=='']
        # print "n-samples: ", len(curr_mvmt)
        # diff_array = np.diff(curr_mvmt)
        pos_diff = curr_mvmt[-1] - curr_mvmt[0]
        print pos_diff


        if acquire_images:
            # if nframes==0 or (nframes % report_period == 0):
            im_array = camera.capture_wait()
            camera.queue_frame()

            if save_images:
                fdict = dict()
                fdict['im'] = im_array
                # fdict['size'] = patch.size[0]
                # fdict['tf'] = driftFrequency
                # fdict['sf'] = patch.sf[0]
                # fdict['ori'] = patch.ori
                fdict['cond'] = cond_labels[int(curr_cond)] #condLabel[int(condType)-1]
                fdict['frame'] = frame_counter
                fdict['refresh'] = n_refresh
                fdict['stimID'] = re.sub('[^%s]' % allow, '', str(stims[stimIdxs[sidx]]))
                # print 'frame #....', frame_counter
                fdict['time'] = datetime.now().strftime(FORMAT)
                fdict['pos'] = patch.pos

                im_queue.put(fdict)

                frame_counter += 1

        # Report num of frames acquired by camera: 
        if nframes % report_period == 0:
            if last_t is not None:
                print('avg frame rate: %f' % (report_period / (t - last_t)))
            last_t = t

        n_refresh += 1
        nframes += 1

        # Break out of the while loop if these keys are registered
        if event.getKeys(keyList=['escape', 'q']):
            raise BreakIt


    expt_dur = globalClock.getTime() - t_expt_start
    print "EXPT DURATION WAS: ", expt_dur

except BreakIt:
    pass    
win.close()

# blockOutputFile.close()
if acquire_images:
    camera.capture_end()
    camera.close()


print "FINISHED"
im_queue.put(None)


ser.close()


if save_images:
    
    hang_time = time.time()
    nag_time = 2.0
    
    sys.stdout.write('Waiting for disk writer to catch up (this may take a while)...')
    sys.stdout.flush()


    while disk_writer.is_alive():
        sys.stdout.write('.')
        sys.stdout.flush()
        # disk_writer.pid(), disk_writer.exitcode()
        time.sleep(nag_time)
    
    print("\n")
    
    print 'disk_writer.isAlive()', disk_writer.is_alive()
    if not im_queue.empty():
        print "NOT EMPTY"
        print im_queue.get()
        print "disk_writer_alive", disk_writer_alive
        print("WARNING: not all images have been saved to disk!")
    else:
        print "EMPTY QUEUE"
    
    
    disk_writer.join()
    print('Disk writer terminated')
    


