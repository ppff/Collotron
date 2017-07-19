#! /usr/bin/python

#########
# Intro #
#########

## Description
# This script works by loading a bunch of images in the current directory,
# cropping them using a clustering algorithm and placing patches randomly
# in order to create a "collage".
# The code is pretty straightforward to follow, don't hesitate to play
# with the parameters!

## Libraries
from skimage import io, segmentation, data, transform
import os, sys
import fnmatch
import numpy as np
import random


#########
# Tools #
#########

## Add alpha layer to RGB image
def add_alpha(img):
	imga = np.zeros((img.shape[0], img.shape[1], 4), dtype=img.dtype)
	imga[:,:,:3] = img[:,:,:3]
	imga[:,:,3] = 1.0 if img.dtype == 'float64' else 255
	return imga

## Get axis aligned bounding box for pixels surrounded buy black pixels
def get_aabb(img):
	rows = np.any(img, axis=1)
	cols = np.any(img, axis=0)
	rmin, rmax = np.where(rows)[0][[0, -1]]
	cmin, cmax = np.where(cols)[0][[0, -1]]
	return img[rmin:rmax+1, cmin:cmax+1]

## Get list of patches from image found with SLIC
def get_patches(img):
	result = []
	segmented = segmentation.slic(img, 
								n_segments=10, 
								compactness=25.0, 
								max_iter=10, 
								sigma=20, 
								spacing=None, 
								multichannel=True, 
								convert2lab=True)
	img = add_alpha(img)

	for i in range(np.amax(segmented)):
		tmp = np.copy(img)
		tmp[segmented[:] != i] = 0
		cropped = get_aabb(tmp)
		result.append(cropped)
	return result

## Resize while preserving aspect ratio, and fixing smallest dimension to 1000
def resize(img):
	ratio = float(img.shape[0]) / float(img.shape[1]) # old x/y
	x = y = 0
	if img.shape[0] <= img.shape[1]:
		x = 1500
		y = int(x/ratio)
	else:
		y = 1500
		x = int(y*ratio)
	return transform.resize(img, (x,y), cval=0)

## Paste patch to image specifying center position for patch, and alpha blend
def paste(img, patch, pos):
	width = patch.shape[0]
	height = patch.shape[1]
	xmin = max(pos[0]-width/2, 0)
	xmax = min(pos[0]+width/2, img.shape[0])
	ymin = max(pos[1]-height/2, 0)
	ymax = min(pos[1]+height/2, img.shape[1])
	difftoxmin = max(0, 0 - (pos[0]-width/2))
	difftoxmax = max(0, (pos[0]+width/2)-(img.shape[0]) )
	difftoymin = max(0, 0 - (pos[1]-height/2))
	difftoymax = max(0, (pos[1]+height/2)-(img.shape[1]) )
	for x in range(xmin,xmax):
		for y in range(ymin,ymax):
			if img[x,y,3] == 0:
				img[x,y] = patch[x-xmin+difftoxmin,y-ymin+difftoymin]
	#img[xmin:xmax, ymin:ymax] = patch[difftoxmin:2*(width/2)-difftoxmax,
	#								  difftoymin:2*(height/2)-difftoymax]
	return img


########
# Main #
########

## Find and open images
img_paths = []
img_paths += fnmatch.filter(os.listdir('.'), '*.jpg')
img_paths += fnmatch.filter(os.listdir('.'), '*.jpeg')
img_paths += fnmatch.filter(os.listdir('.'), '*.png')

images = io.imread_collection(img_paths)

## Resize images
# note: this is done to harmonize the size of patches, 
# although it is not mandatory
images = [resize(img) for img in images]
print 'Loaded {} images'.format(len(images))

## Extract patches
# Clusters are found using kmeans which outputs masks
# which are used to extract and crop clusters on transparent background
#img = images[0]
#patches = get_patches(img)
patches = [p for img in images for p in get_patches(img)]
print 'Extracted {} patches'.format(len(patches))

## Place patches
# > select a random patch
# > place it at a random location
# > select a new random patch
# > place it somewhere that's still not filled
# > repeat until everything is filled
while 1:
	collage = np.zeros((1000, 1000, 4))
	while np.any(collage[:,:,3]==0):
		# select patch
		patch = random.choice(patches)
		# place it
		empty_pixels = np.where(collage[:,:,3]==0)
		position = [random.choice(empty_pixels[0]), 
					random.choice(empty_pixels[1])]
		print " > Pasting patch " + str(patches.index(patch)) \
			+ " at " + str(position)
		collage = paste(collage, patch, position)

	print "Over! File written to collage.jpg"
	io.imsave("collage.jpg", collage)
	io.imshow(collage)
	io.show()

