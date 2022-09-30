#!/bin/bash

# =============================================================================
# Author: Gerard Martí
# Description: Apply FastSurfer pipeline to a T1 image
# adapted from TVB-pipeline by Schirner et al
# =============================================================================

# Input
subID=$1
t1=$2
out_dir=$3

# Check input
rootPath=$(pwd)

export FREESURFER_HOME=/usr/local/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

FastSurferDir=/home/extop/lib/FastSurfer
export FASTSURFER_HOME=${FastSurferDir}

FSLDIR=/usr/local/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH

MRTrixDIR=/home/extop/lib/mrtrix3/bin
export PATH=${MRTrixDIR}:${PATH}

#############################################################

# change to working directory

echo "*** Load data & recon_all for FASTSurfer ***"

## RUN FASTSURFER
# use no cuda to be able to parallelize without clogging the gpu
# only use for amsterdam
# fslmaths ${t1} -mas ${t1} ${out_dir}/t1_pos.nii.gz

${FastSurferDir}/run_fastsurfer.sh --t1 ${t1} --sid recon_all --sd ${out_dir} --py python --no_cuda
# 
echo "*** Adapt filenames and folders to FreeSurfer output so that next scripts works flawlessly ***"

rename 's/\.mapped//' ${out_dir}/recon_all/*/*
rename 's/\.deep//' ${out_dir}/recon_all/*/*

mrconvert -force ${out_dir}/recon_all/mri/brain.mgz ${out_dir}/recon_all/mri/brain.nii.gz
mrconvert -force ${out_dir}/recon_all/mri/T1.mgz ${out_dir}/recon_all/mri/T1.nii.gz
mrconvert -force ${out_dir}/recon_all/mri/aparc.DKTatlas+aseg.mgz ${out_dir}/recon_all/mri/aparc.DKTatlas+aseg.nii.gz

# norm
mrconvert -force ${out_dir}/recon_all/mri/norm.mgz ${out_dir}/recon_all/mri/norm.nii.gz