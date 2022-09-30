"""
Quick python script to generate slicetimes.txt for milan

acquired in descending order (“from head to foot”) and using a simultaneous multi-slice factor (multi-band)=2

So, slices were acquired in this order:

1 & 25
2 & 26
3 & 27
.. and so on till
24 & 48

1
25
2
26
3
27
4
28

From: [https://en.wikibooks.org/wiki/SPM/Slice_Timing#Multiband_EPI_acquisitions](https://en.wikibooks.org/wiki/SPM/Slice_Timing#Multiband_EPI_acquisitions)

"If you do know your slice order but not your slice timing, 
you can artificially create a slice timing manually, by generating artificial values from the slice order with equal 
temporal spacing, and then scale the numbers on the TR, so that the last temporal slices timings = TR - TR/(nslices/multiband_channels)."
"""

import json
import os
import argparse
parser = argparse.ArgumentParser(description="Setup all parameters for slice time correction file generation for MILAN dataset")
parser.add_argument("jsonfile",help="location of json file .")
parser.add_argument("--slicetime",help="name and location to place slice timing file with slice times for each slice acquired.")
args=parser.parse_args()

if args.slicetime:
	slicetimefile=os.path.abspath(args.slicetime)
else:
	slicetimefile=os.path.join(os.getcwd(),'slicetimes.txt')

multiband_channels = 2
nslices = 48
json_file=open(args.jsonfile)
info = json.load(json_file)
TR=float(info['RepetitionTime'])
reftime=TR/2

slicelist = [ (sliceidx+1, ( (sliceidx+1)*TR/(nslices/multiband_channels) - reftime) ) for sliceidx in range( int(nslices/multiband_channels) ) ]

lst_temporal_slice = TR - TR/(nslices/multiband_channels)
slicelist2 = [(x+24, y) for (x,y) in slicelist]
slicelistfull = slicelist + slicelist2

sortedSlices = sorted(slicelistfull, key=lambda tup: tup[1])
slicetimes=[str(sliceinfo[1]) for sliceinfo in slicelistfull]
slicenums=[str(sliceinfo[0]) for sliceinfo in sortedSlices]

# compute slicetimes
slicetimef=open(slicetimefile,'w')
slicetimef.write("\n".join(slicetimes))
slicetimef.close()