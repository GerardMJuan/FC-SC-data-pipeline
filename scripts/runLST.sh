#!/bin/bash

# =============================================================================
# Description: Run LST toolbox from MATLAB rto 
# adapted from TVB-pipeline by Schirner et al
# =============================================================================

# load MATLAB
# and SPM12

spm_folder=
matlab_path=
export PATH=$matlab_path:$PATH


subjID=$1
t1_path=$2
flair_path=$3
out_dir=$4
type_dir=$5

cd $out_dir

mkdir -p $out_dir/lst/

cp $t1_path $out_dir/lst/T1.nii.gz
cp $flair_path $out_dir/lst/FLAIR.nii.gz

t1_path=$out_dir/lst/T1.nii.gz
flair_path=$out_dir/lst/FLAIR.nii.gz

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

# copy to the original directory
cp $out_lesion ${type_dir}/${subjID}/${subjID}_ROI.nii.gz