#!/bin/bash

# =============================================================================
# Author: Gerard Martí
# Description: Process the DT image and create the full brain tracking, which
# will be preprocessed later
# =============================================================================

################################################
## LIBRARIES
################################################
# configuration
# Check input
rootPath=$(pwd)

export FREESURFER_HOME=/usr/local/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export ANTSPATH=
export PATH=${ANTSPATH}:$PATH

FSLDIR=/usr/local/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH

MRTrixDIR=
export PATH=${MRTrixDIR}:${PATH}

export PATH=/usr/local/cuda-10.2/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-10.2/lib64:$LD_LIBRARY_PATH

################################################
## INPUT FILES
################################################

# subject path

subID=$1 
subj_path=$2
dwi=$3
dwi2=$4 # NEEDED FOR EPI CORRECTION, COULD BE NONE
bval=$5
bvec=$6
lesions_roi=$7
type_data=$8
fm_phase=$9
fm_magnitude=${10}
json=${11}
bval2=${12}
bvec2=${13}

#SIEMENS DEFAULT
# these are parameters that depend on the scanner
# BOTH IN MS
# probably should be input
# TE=103 # DTI TE
# DT=0.485 # dwell time 

# FREESURFER PATH
# path where the freesurfer is
fs_path=${subj_path}/recon_all
# create directory
out_dir=${subj_path}/dt_proc
mkdir $out_dir -p

################################################
## PREPROCESS DWI IMAGE
################################################

# CREATE B0 FILE OF ORIGINAL
dwiextract $dwi -fslgrad $bvec $bval - -bzero | mrmath - mean ${out_dir}/dwi_b0.mif -axis 3
mrconvert ${out_dir}/dwi_b0.mif ${out_dir}/dwi_b0.nii.gz

# generate the mask
mrconvert -force $dwi ${out_dir}/dwi.mif

## DENOISING
dwidenoise ${out_dir}/dwi.mif ${out_dir}/dwi_den.mif -noise ${out_dir}/noise.mif -force -nthreads 4

## GIBBS RINGING REMOVAL
mrdegibbs ${out_dir}/dwi_den.mif ${out_dir}/dwi_den_unr.mif -axes 0,1 -nthreads 4

# use dti_preproc script 
mrconvert -force ${out_dir}/dwi_den_unr.mif ${out_dir}/dwi_den_unr.nii.gz

if [ "$type_data" = "CLINIC" ]; then

    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    -rpe_none -pe_dir j- -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -nthreads 4 -force #  ## -pe_dir ap # 

    #### FUGUE
    bet $fm_magnitude ${out_dir}/fm_mag_ero.nii.gz -m -f 0.55
    fslmaths ${out_dir}/fm_mag_ero.nii.gz -ero ${out_dir}/fm_mag_ero.nii.gz
    fslmaths ${out_dir}/fm_mag_ero_mask.nii.gz -ero ${out_dir}/fm_mag_ero_mask.nii.gz

    fsl_prepare_fieldmap SIEMENS $fm_phase ${out_dir}/fm_mag_ero.nii.gz ${out_dir}/fieldmap.nii 2.46

    fslmaths ${out_dir}/fieldmap.nii -mas ${out_dir}/fm_mag_ero_mask.nii.gz ${out_dir}/fieldmap_brain.nii.gz
    fugue --loadfmap=${out_dir}/fieldmap_brain.nii.gz -s 4 --savefmap=${out_dir}/fieldmap_brain_s4.nii.gz

    # fugue --loadfmap=FieldMap/FieldMap_brain -s 4 --savefmap=FieldMap/FieldMap_brain_s4
    fugue -v -i ${out_dir}/fm_mag_ero.nii.gz --unwarpdir=y- --dwell=0.000485 --nokspace --loadfmap=${out_dir}/fieldmap.nii -w ${out_dir}/fm_mag_ero_warped.nii.gz
    flirt -in ${out_dir}/fm_mag_ero_warped.nii.gz -ref ${out_dir}/dwi_den_unr_ec.nii.gz -out ${out_dir}/fm_mag_ero_warped2dti.nii.gz -omat ${out_dir}/fieldmap2diff.mat
    flirt -in ${out_dir}/fieldmap_brain_s4.nii.gz -ref ${out_dir}/dwi_den_unr_ec.nii.gz -applyxfm -init ${out_dir}/fieldmap2diff.mat -out ${out_dir}/fieldmap_warped.nii
    # fugue -v -i DTI/data1_corr.nii.gz --icorr --unwarpdir=y --dwell=0.000485 --loadfmap=FieldMap/FieldMap_brain_s4_2_nodif_brain.nii.gz -u data/data.nii.gz

    fugue -v -i ${out_dir}/dwi_den_unr_ec.nii.gz --icorr --dwell=0.000485 --loadfmap=${out_dir}/fieldmap_warped.nii --unwarpdir=y- -u ${out_dir}/dwi_den_unr_epi_ec.nii.gz

    # fslpreproc
    # dwifslpreproc ${out_dir}/dwi_den_unr_epi.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    # -rpe_none -pe_dir j- -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -nthreads 8 -force #  ## -pe_dir ap # 

elif [ "$type_data" = "MAINZ" ]; then
    # only fslpreproc
    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    -rpe_none -pe_dir j- -json_import ${json} -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

elif [ "$type_data" = "MILAN" ]; then
    ## CREATE DUAL B0
    # USE ALIGN SEEPI
    # mrmath ${out_dir}/dwi_den_unr.mif mean ${out_dir}/dwi_b0_og.mif -axis 3
    dwiextract ${out_dir}/dwi_den_unr.mif -fslgrad $bvec $bval - -bzero -force | mrmath - mean ${out_dir}/dwi_b0_og.mif -axis 3 -force

    ## add a 0 b0 file
    echo '0 0 0 0' > ${out_dir}/b0grad.txt
    
    mrmath $dwi2 mean ${out_dir}/dwi_b0_2.nii.gz -axis 3 -force
    # fslroi $dwi2 ${out_dir}/dwi_b0_2.nii.gz 0 1
    mrconvert ${out_dir}/dwi_b0_2.nii.gz -grad ${out_dir}/b0grad.txt ${out_dir}/dwi_b0_2.mif -force
    # dwiextract $dwi2 -grad ${out_dir}/b0grad.txt - -bzero | mrmath - mean ${out_dir}/dwi_b0_2.mif -axis 3

    # USE UNPROCESSED B0 (dwi_b0.mif) instead of processed one
    mrcat ${out_dir}/dwi_b0_og.mif ${out_dir}/dwi_b0_2.mif ${out_dir}/b0_pair.mif -axis 3 -force
    
    #IT DOESNT GET READOUT TIME FROM JSON (NOT A BIG DEAL RIGHT)
    # amb 0.02 anava molt bé
    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear --data_is_shelled" \
    -rpe_pair -se_epi ${out_dir}/b0_pair.mif -pe_dir j -json_import ${json} -readout_time 0.0828 -align_seepi -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

    # dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear --data_is_shelled" \
    # -rpe_none -pe_dir j -json_import ${json} -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

    fslmaths ${out_dir}/dwi_den_unr_epi_ec.nii.gz -mul -1 -bin -mul 0.00001 ${out_dir}/dwi_den_unr_epi_ec_add.nii.gz
    fslmaths ${out_dir}/dwi_den_unr_epi_ec.nii.gz -thr 0 -add ${out_dir}/dwi_den_unr_epi_ec_add.nii.gz ${out_dir}/dwi_den_unr_epi_ec.nii.gz

elif [ "$type_data" = "NAPLES" ]; then
    # only fslpreproc
    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    -rpe_none -pe_dir j- -json_import ${json} -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

elif [ "$type_data" = "OSLO" ]; then
    ## CREATE DUAL B0
    # USE ALIGN SEEPI
    dwiextract ${out_dir}/dwi_den_unr.mif -fslgrad $bvec $bval - -bzero | mrmath - mean ${out_dir}/dwi_b0_og.mif -axis 3
    dwiextract $dwi2 -fslgrad $bvec2 $bval2 - -bzero | mrmath - mean ${out_dir}/dwi_b0_2.mif -axis 3

    mrcat ${out_dir}/dwi_b0_og.mif ${out_dir}/dwi_b0_2.mif ${out_dir}/b0_pair.mif -axis 3
    # theoretically, it will get readout time from the json
    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    -rpe_pair -se_epi ${out_dir}/b0_pair.mif -pe_dir j -json_import ${json} -align_seepi -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

elif [ "$type_data" = "AMSTERDAM" ]; then
    # only fslpreproc
    dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
    -rpe_none -pe_dir j- -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

elif [ "$type_data" = "LONDON" ]; then

    # if we have a _rev file, then we can do RPE_PAIR
    if [ -f $dwi2 ]; then
        dwiextract ${out_dir}/dwi_den_unr.mif -fslgrad $bvec $bval - -bzero -force | mrmath - mean ${out_dir}/dwi_b0_og.mif -axis 3 -force

        ## add a 0 b0 file
        echo '0 0 0 0' > ${out_dir}/b0grad.txt
        
        # mrmath $dwi2 mean ${out_dir}/dwi_b0_2.nii.gz -axis 3 -force
        # fslroi $dwi2 ${out_dir}/dwi_b0_2.nii.gz 0 1
        mrconvert $dwi2 -grad ${out_dir}/b0grad.txt ${out_dir}/dwi_b0_2.mif -force
        # dwiextract $dwi2 -grad ${out_dir}/b0grad.txt - -bzero | mrmath - mean ${out_dir}/dwi_b0_2.mif -axis 3

        # USE UNPROCESSED B0 (dwi_b0.mif) instead of processed one
        mrcat ${out_dir}/dwi_b0_og.mif ${out_dir}/dwi_b0_2.mif ${out_dir}/b0_pair.mif -axis 3 -force
        
        #IT DOESNT GET READOUT TIME FROM JSON (NOT A BIG DEAL RIGHT)
        # amb 0.02 anava molt bé
        dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear --data_is_shelled" \
        -rpe_pair -se_epi ${out_dir}/b0_pair.mif -pe_dir j -json_import ${json} -align_seepi -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

        ######### IF MILAN, THEN CREATE AN EXTRA DT_RECON
        # AND IF LONDON, do it too
        dwiextract ${out_dir}/dwi_den_unr_epi_ec.nii.gz ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii.gz -fslgrad $bvec $bval -shells 0,1000 -export_grad_fsl ${out_dir}/bvecs_milan_ec.bvec ${out_dir}/bvecs_milan_ec.bval
        mrconvert ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii.gz ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii -force
        dt_recon --i ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii --b ${out_dir}/bvecs_milan_ec.bval ${out_dir}/bvecs_milan_ec.bvec --sd ${subj_path} --s recon_all --o ${subj_path}/dt_recon_lowshell --no-ec 

    else
        # if not,
        # only fslpreproc
        dwifslpreproc ${out_dir}/dwi_den_unr.nii.gz  ${out_dir}/dwi_den_unr_epi_ec.nii.gz -fslgrad $bvec $bval -eddy_options " --slm=linear" \
        -rpe_none -pe_dir j -export_grad_fsl ${out_dir}/bvecs_ec.bvec ${out_dir}/bvals_ec.bval -force -nthreads 4

    fi
fi
## DWIFSLPREPROC CREATES NEW BVAL AND BVEC, MAKE SURE THAT THEY ARE UPDATED
bval=${out_dir}/bvals_ec.bval
bvec=${out_dir}/bvecs_ec.bvec

# RUN FREESURFER'S DT RECON
# no EC BECAUSE WE ALWAYS RUN FSLPREPROC

######### IF MILAN, THEN CREATE AN EXTRA DT_RECON
# AND IF LONDON, do it too
# if [ "$type_data" = "LONDON" ]; then
#     dwiextract ${out_dir}/dwi_den_unr_epi_ec.nii.gz ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii.gz -fslgrad $bvec $bval -shells 0,1000 -export_grad_fsl ${out_dir}/bvecs_milan_ec.bvec ${out_dir}/bvecs_milan_ec.bval
#     mrconvert ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii.gz ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii -force
#     dt_recon --i ${out_dir}/dwi_den_unr_epi_ec_lowshell.nii --b ${out_dir}/bvecs_milan_ec.bval ${out_dir}/bvecs_milan_ec.bvec --sd ${subj_path} --s recon_all --o ${subj_path}/dt_recon_lowshell --no-ec 
# fi

mrconvert ${out_dir}/dwi_den_unr_epi_ec.nii.gz ${out_dir}/dwi_den_unr_epi_ec.nii -force
dt_recon --i ${out_dir}/dwi_den_unr_epi_ec.nii --b $bval $bvec --sd ${subj_path} --s recon_all --o ${subj_path}/dt_recon --no-ec 

# register T1
lowb=${subj_path}/dt_recon/lowb.nii.gz
rule=${subj_path}/dt_recon/register.dat

mri_vol2vol --mov $lowb --targ ${subj_path}/recon_all/mri/T1.nii.gz  --inv --interp trilin --o ${out_dir}/norm2diff.nii --reg $rule --no-save-reg

#######################################
## HERE BVEC AND BVAL NEED TO BE UPDATED WITH THE NEW ONES IN DT_RECON
#######################################

## BIAS CORRECT
mrconvert -force ${subj_path}/dt_recon/dwi.nii.gz ${subj_path}/dt_recon/dwi.mif
dwibiascorrect ants ${subj_path}/dt_recon/dwi.mif ${subj_path}/dt_recon/dwi-ec_unbiased.mif -bias ${out_dir}/bias.mif -fslgrad $bvec $bval -nthreads 4

################################################
## PREPARE REGIONS FOR TRACKING
################################################

mrconvert -force ${subj_path}/dt_recon/dwi-ec_unbiased.mif ${out_dir}/dwi_ec_unbiased.nii.gz

# CREATE MASK
dwi2mask ${out_dir}/dwi_ec_unbiased.nii.gz -fslgrad $bvec $bval - | mrconvert -force - ${out_dir}/dwi_ec_unbiased_mask.nii.gz

# find the response using dhollander altogrithm
dwi2response dhollander ${out_dir}/dwi_ec_unbiased.nii.gz -fslgrad $bvec $bval \
-mask ${out_dir}/dwi_ec_unbiased_mask.nii.gz ${out_dir}/wm.txt ${out_dir}/gm.txt ${out_dir}/csf.txt -voxels ${out_dir}/voxels.mif -force -nthreads 4

# differentiate between wm and csf (have only 2 bval for the datasets that I have), except for MILAN (do it manually)
t=$(tr ' ' '\n' < $bval | sort | uniq -c | wc -l)
t="$(($t-1))"

# if we have 3 or more bvals, we can do 3 tissues msmt_csd
if [ "$t" -ge 3 ]; then
    dwi2fod msmt_csd ${out_dir}/dwi_ec_unbiased.nii.gz -fslgrad $bvec $bval -mask ${out_dir}/dwi_ec_unbiased_mask.nii.gz \
    ${out_dir}/wm.txt ${out_dir}/wmfod.mif ${out_dir}/gm.txt ${out_dir}/gm.mif ${out_dir}/csf.txt ${out_dir}/csffod.mif -nthreads 4
else
    dwi2fod msmt_csd ${out_dir}/dwi_ec_unbiased.nii.gz -fslgrad $bvec $bval -mask ${out_dir}/dwi_ec_unbiased_mask.nii.gz \
    ${out_dir}/wm.txt ${out_dir}/wmfod.mif ${out_dir}/csf.txt ${out_dir}/csffod.mif -nthreads 4
fi

################################################
## CREATE 5TT AND BRING IN TO DWI SPACE
################################################
##### THIS HAS BEEN CHANGED TO TRY 5TTFSL

# use freesurfer's compute volume fractions to obtain all parts
SUBJECTS_DIR=${subj_path}

# 5ttgen fsl ${subj_path}/recon_all/mri/norm.nii.gz ${out_dir}/5ttfsl.nii.gz -premasked -nocrop -sgm_amyg_hipp -force
# 5ttgen hsvs ${subj_path}/recon_all ${out_dir}/5ttfsl.nii.gz -hippocampi aseg -thalami aseg -nocrop -sgm_amyg_hipp -white_stem -force

mri_compute_volume_fractions --o ${out_dir}/5tt --regheader recon_all ${subj_path}/recon_all/mri/norm.mgz \
 --nii.gz --seg aparc.DKTatlas+aseg.mgz
 
# create empty file for last part of 5tt
fslmaths ${out_dir}/5tt.cortex.nii.gz -mul 0 ${out_dir}/empty.nii.gz 

# concatenate to create 5tt
mrcat ${out_dir}/5tt.cortex.nii.gz ${out_dir}/5tt.subcort_gm.nii.gz ${out_dir}/5tt.wm.nii.gz ${out_dir}/5tt.csf.nii.gz ${out_dir}/empty.nii.gz ${out_dir}/5tt_fs.nii.gz 

if [ -f "$lesions_roi" ]; then
    # convert lesions to standard
    mri_convert -c -rt nearest ${lesions_roi} ${out_dir}/r${subID}_ROI_00_256.nii.gz

    # do a small dilation of the mask
    fslmaths ${out_dir}/r${subID}_ROI_00_256.nii.gz -kernel 3D -dilM ${out_dir}/lesions_dilated_std.nii.gz

    # edit 5tt
    # changed to ffsl
    5ttedit ${out_dir}/5tt_fs.nii.gz ${out_dir}/5tt_fs.nii.gz -path ${out_dir}/lesions_dilated_std.nii.gz -force
fi

# register 5tt to dt image
#mri_vol2vol --mov $lowb --targ ${out_dir}/5ttfsl.nii.gz  --inv --interp trilin --o ${out_dir}/5tt2diff.nii.gz --reg $rule --no-save-reg

#5tt2gmwmi ${out_dir}/5tt2diff.nii.gz ${out_dir}/gmwmSeed_coreg.mif

# register 5tt to dt image
mri_vol2vol --mov $lowb --targ ${out_dir}/5tt_fs.nii.gz  --inv --interp nearest --o ${out_dir}/5tt2diff.nii --reg $rule --no-save-reg

# number of streamlines
num_streamlines=6000000

# Extract brainstem
fslmaths ${fs_path}/mri/aparc.DKTatlas+aseg.nii.gz -uthr 16 -thr 16 -bin ${out_dir}/brainstem.nii.gz

# register brainstem
mri_vol2vol --mov $lowb --targ ${out_dir}/brainstem.nii.gz --inv --interp nearest --o ${out_dir}/brainstem2diff.nii.gz --reg $rule --no-save-reg

# RUN TCKGEN
# recommended not to use mask (check documentation ACT)
# -mask ${out_dir}/dwi_ec_unbiased_mask.nii.gz
tckgen ${out_dir}/wmfod.mif ${out_dir}/brain_track.tck -algorithm iFOD2 -seed_image \
${out_dir}/dwi_ec_unbiased_mask.nii.gz -select 6000000 -nthreads 6 \
-fslgrad $bvec $bval -act ${out_dir}/5tt2diff.nii -backtrack -cutoff 0.06 -crop_at_gmwmi -exclude ${out_dir}/brainstem2diff.nii.gz -force

#tckgen ${out_dir}/wmfod.mif ${out_dir}/brain_track.tck -algorithm iFOD2 -seed_gmwmi ${out_dir}/gmwmSeed_coreg.mif -select 6000000 -nthreads 6 \
#-fslgrad $bvec $bval -act ${out_dir}/5tt2diff.nii.gz -backtrack -cutoff 0.06 -crop_at_gmwmi -force

# ## CREATE B0 FILE TO CHEKC REGISTRATION
dwiextract ${out_dir}/dwi_ec_unbiased.nii.gz -fslgrad $bvec $bval - -bzero | mrmath - mean ${out_dir}/mean_b0_preprocessed.mif -axis 3
mrconvert ${out_dir}/mean_b0_preprocessed.mif ${out_dir}/mean_b0_preprocessed.nii.gz

# # create 5tt to viusalize
mrconvert ${out_dir}/5tt2diff.nii ${out_dir}/5tt2diff.mif
5tt2vis ${out_dir}/5tt2diff.mif ${out_dir}/5tt2diff_3d.mif
mrconvert ${out_dir}/5tt2diff_3d.mif ${out_dir}/5tt2diff_3d.nii.gz

# #### REMOVE FILES
rm ${out_dir}/mean_b0_preprocessed.mif -f
rm ${out_dir}/0000.nii.gz -f
rm ${out_dir}/0001.nii.gz -f
rm ${out_dir}/0002.nii.gz -f
rm ${out_dir}/0003.nii.gz -f
rm ${out_dir}/0004.nii.gz -f
rm ${out_dir}/dwi_den.mif -f
rm ${out_dir}/dwi_den_unr.mif -f
rm ${out_dir}/dwi_den_unr.nii.gz -f
rm ${out_dir}/dwi_den_unr_fugue.nii.gz -f
rm ${out_dir}/empty.nii.gz -f
rm ${out_dir}/5tt2diff.mif -f
rm ${out_dir}/5tt2diff_3d.mif -f

# remove possible temporal files (if they appear)
rm dwi2response* -rf
rm dwibiascorrect* -rf 

# norm (if not done by fastsurfer script)
mrconvert ${fs_path}/mri/norm.mgz ${fs_path}/mri/norm.nii.gz