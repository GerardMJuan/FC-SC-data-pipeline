#!/bin/bash

# =============================================================================
# Author: Gerard Martí
# Description: Run LST toolbox from MATLAB rto 
# adapted from TVB-pipeline by Schirner et al
# =============================================================================

# load MATLAB
# and SPM12

spm_folder='/home/extop/lib/spm12'

export PATH=/home/extop/lib/MATLAB/R2021b/bin/:$PATH

# t1_path='/mnt/DADES/Gerard/DATA/LST_TESTING/CLINIC/rFIS_063_T1_00.nii'
# flair_path='/mnt/DADES/Gerard/DATA/LST_TESTING/CLINIC/rFIS_063_FLAIR_00.nii'

subjID=$1
t1_path=$2
flair_path=$3
out_dir=$4
type_dir=$5

cd $out_dir

mkdir -p $out_dir/lst/

cp $t1_path $out_dir/lst/T1.nii.gz
cp $flair_path $out_dir/lst/FLAIR.nii.gz
# cp $lesion_path $out_dir/lst/lesion.nii.gz

t1_path=$out_dir/lst/T1.nii.gz
flair_path=$out_dir/lst/FLAIR.nii.gz
# lesion_path=$out_dir/lst/lesion.nii.gz

# ONLY AMSTERDAM
# TO WORK WITH T1
if [ "$type_dir" = "AMSTERDAM" ]; then
    fslmaths ${t1_path} -mas ${t1_path} $out_dir/lst/T1_pos.nii.gz
    t1_path=$out_dir/lst/T1_pos.nii.gz
fi

# other version is ps_LST_lpa
matlab -nodisplay -nosplash -r "cd '$out_dir';addpath(genpath('$spm_folder'));ps_LST_lga('$t1_path','$flair_path',0.3,1,50);quit;"

#this always generates a file
out_lesion=$out_dir/lst/${subjID}_ROI.nii.gz # need to be same format, or similar, to the clinic ones
lesion_path=$out_dir/lst/ples_lga_0.3_rmFLAIR.nii.nii # double NII i dont know why
flair_path=$out_dir/lst/rmFLAIR.nii
cp $lesion_path $out_dir/lst/${subjID}_ROI.nii
gzip $out_dir/lst/${subjID}_ROI.nii
# register FLAIR to T1 and apply to lesions ROI
# with the output name being
# flirt -in $flair_path -ref $t1_path -omat $out_dir/lst/FLAIR2T1.mat -out $out_dir/lst/FLAIR2T1.nii

# TODO. CURRENTLY, LESION PATH IS NOT DEFINED. NEEDS TO BE FOUND BY GETTING THE OUTPUT OF THE MATLAB FUNCTION
# flirt -in $lesion_path -ref $t1_path -init $out_dir/lst/FLAIR2T1.mat -applyxfm -out $out_lesion 

# copy to the original directory
# HARDCODED
cp $out_lesion /mnt/nascarm01/data/Projectes/MAGNIMS2021/${type_dir}/${subjID}/${subjID}_ROI.nii.gz