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
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import os

def make_fsl(jsonfile, slicetime, slicenum):
    """
    Setup all parameters for slice time correction file generation for FSL

    jsonfile: location of json file provided by dcm2niix -b during dicom conversion
    slicetime: name and location to place slice timing file with slice times for each slice acquired
    slicenum: name and location to place slice timing file with slices in order of acquisition
    
    """
    if slicetime:
        slicetimefile=os.path.abspath(slicetime)
        doSliceTime = True
    elif not slicenum:
        slicetimefile=os.path.join(os.getcwd(),'slicetimes.txt')
        doSliceTime = True

    if slicenum:
        slicenumfile=os.path.abspath(slicenum)
        doSliceNum = True
    elif not slicetime:
        slicenumfile=os.path.join(os.getcwd(),'sliceorder.txt')
        doSliceNum = True

    json_file=open(jsonfile)
    info = json.load(json_file)
    slicetime=info['SliceTiming']
    TR=float(info['RepetitionTime'])
    reftime=TR/2
    slicelist = [ (sliceidx+1,(float(sliceval) - reftime)/TR, sliceval) for sliceidx,sliceval in enumerate(slicetime)]

    sortedSlices = sorted(slicelist, key=lambda tup: tup[1])

    slicetimes=[str(sliceinfo[1]) for sliceinfo in slicelist]
    slicenums=[str(sliceinfo[0]) for sliceinfo in sortedSlices]

    if doSliceTime:
        slicetimef=open(slicetimefile,'w')
        slicetimef.write("\n".join(slicetimes))

    if doSliceNum:
        slicenumf=open(slicenumfile,'w')
        slicenumf.write("\n".join(slicenums))

def make_milan(jsonfile, slicetime):
    """
    Setup all parameters for slice time correction file generation for MILAN dataset

    jsonfile: location of json file
    slicetime: name and location to place slice timing file with slice times for each slice acquired    
    """

    if slicetime:
        slicetimefile=os.path.abspath(slicetime)
    else:
        slicetimefile=os.path.join(os.getcwd(),'slicetimes.txt')

    multiband_channels = 2
    nslices = 48
    json_file=open(jsonfile)
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