#!/usr/bin/env python2

import os

# 1.  Create frame or image arrays, and then store in some tmp directory.

path_to_frames = "/path/to/frames" 
# all the frames names should be in the same format (e.g., "image0001.png", "image0002.png", etc.)
# use string formatting syntax to specify (e.g., %04d.png)

# 2.  Grab all the frames from above path and create mp4. Need to install ffmpeg. If using python, I'd recommend creating an anaconda environment and doing "pip install ffmpeg"

path_to_movie = "/path/to/movies"
# include path to save output movie -- the settings below work for mp4
# look up options for ffmpeg to see what else can be used

os.system("ffmpeg -r 120 -f image2 -i %s/image%04d.png -vcodec libx264 -pix_fmt yuv420p %s/movie.mp4" % (path_to_frames, path_to_movie))

# Alternatively, you can use cv2 packages to iteratively add frames to your movie.