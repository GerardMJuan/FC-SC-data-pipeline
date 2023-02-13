#!/bin/bash

# =============================================================================
# Author: Gerard Martí
# Description: Runs a few commands to do quality control of the tracking,
# generating relevant images that show the tracking generated 
# =============================================================================

# configuration
export FREESURFER_HOME=/usr/local/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export ANTSPATH=/home/extop/lib/ANTs/bin
export PATH=${ANTSPATH}:$PATH

FSLDIR=/usr/local/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH

MRTrixDIR=/home/extop/lib/mrtrix3/bin
export PATH=${MRTrixDIR}:${PATH}

# inputs
subject_dir=$1
output_dir=$2

# images
dwi_proc=$subject_dir/dt_proc/mean_b0_preprocessed.nii.gz
tracks_AEC=$subject_dir/dt_proc/brain_track_AEC.tck
sift_weights=$subject_dir/dt_proc/brain_track.txt

tracks_AEC_600=$subject_dir/dt_proc/brain_track_AEC_600.tck

# compute small tracks for tracks and tracks AEC, with AEC including SIFT (final version of the connectome)
tckedit $tracks_AEC -tck_weights_in $sift_weights $tracks_AEC_600 -force

# run mrview to visualize the tracking (the small fibers one, not the full one)
# capture the values

mrview -load $dwi_proc -voxel 85,76,49 -mode 2 -tractography.load $tracks_AEC_600 -capture.folder $output_dir \
 -capture.prefix track_AECSIFT -capture.grab -exit

# full track AEC
# image of fraction of streamlines from each voxel
tckmap $tracks_AEC_600 -vox 1.0 - | mrcalc - $(tckinfo $tracks_AEC_600 | grep "count" | cut -d':' -f2 | tr -d '[:space:]') -div $output_dir/tdi_fractional_AEC.mif
mrconvert -force $output_dir/tdi_fractional_AEC.mif $output_dir/track_tdi_fractional_AEC.nii.gz

# streamline count per voxel
tckmap $tracks_AEC_600 -vox 1.0 $output_dir/tdi_count_AEC.mif
mrconvert -force $output_dir/tdi_count_AEC.mif $output_dir/track_tdi_count_AEC.nii.gz
