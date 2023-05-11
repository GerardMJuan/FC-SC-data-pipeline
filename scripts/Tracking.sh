#!/bin/bash

# =============================================================================
# Author: Gerard Martí, Eloy Martínez de las Heras
# Description: Implements pipeline to extract SC weights and length tracts from 
# generated tractography, using a segmentation based on freesurfer
# NOTE: it is required to change the labels of the segmentation beforehand, using
# script change_segmentation.py
# Based on https://doi.org/10.1371/journal.pone.0137064
# =============================================================================

# configuration
export FREESURFER_HOME=
source $FREESURFER_HOME/SetUpFreeSurfer.sh

export ANTSPATH=
export PATH=${ANTSPATH}:$PATH

FSLDIR=/usr/local/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH

MRTrixDIR=
export PATH=${MRTrixDIR}:${PATH}
export MRTRIX_QUIET=Y

## RELEVANT PATHS (may be entered by args?)
subID=$1
subj_path=$2

out_dir=${subj_path}/dt_proc # should already be created
FS=${subj_path}/recon_all

#subID="FIS_028" 

# relevant files for registering
lowb=${subj_path}/dt_recon/lowb.nii.gz
rule=${subj_path}/dt_recon/register.dat

# remove temporal files
rm -rf ${out_dir}/nodes
rm -rf ${out_dir}/tck

mkdir -p ${out_dir}/nodes
mkdir -p ${out_dir}/tck

size="$(fslval ${subj_path}/dt_recon/fa.nii.gz pixdim3)"
size_thr=`echo $size + 0.5 | bc`

# needs to be updated with the values of the mindboggle UI
# THIS NEEDS TO BE RUN BEFORE CALLING THIS SCRIPT, IN PYTHON
fslchfiletype NIFTI_GZ ${FS}/mri/aparc.DKTatlas+aseg_newSeg.nii.gz

# transform the atlas to dwi space
mri_vol2vol --mov $lowb --targ ${FS}/mri/aparc.DKTatlas+aseg_newSeg.nii.gz --inv --interp nearest --o ${out_dir}/nodes2diff.nii.gz --reg $rule --no-save-reg

# tambe transform anatomical to diff
# is T1 in nii format?
mrconvert -force ${FS}/mri/T1.mgz ${FS}/mri/T1.nii.gz
mri_vol2vol --mov $lowb --targ ${FS}/mri/T1.nii.gz --inv --interp trilin --o ${out_dir}/anat2diff.nii.gz --reg $rule --no-save-reg

# create binary mask of all the
fslmaths ${out_dir}/nodes2diff -bin ${out_dir}/nodes2diff_bin

# create binary mask for each area of the atlas
for i in {1..76};do
    fslmaths ${out_dir}/nodes2diff -thr ${i} -uthr ${i} -bin ${out_dir}/nodes/${i}
done

# Generate a connectome matrix from a streamlines file and a node parcellation image
tck2connectome ${out_dir}/brain_track.tck ${out_dir}/nodes2diff.nii.gz ${out_dir}/connectome.csv \
-out_assignments ${out_dir}/assignments.csv -assignment_radial_search $size_thr -force -nthreads 6

# Create a file for each connection between rois
connectome2tck ${out_dir}/brain_track.tck ${out_dir}/assignments.csv ${out_dir}/tck/${subID}-- -exclusive -force -nthreads 6

rm -f ${out_dir}/assignments.csv
rm -f ${out_dir}/connectome.csv

## CREATE AND PRUNE CONNECTOME BETWEEN EACH PAIR OF REGIONS
# NOT ONLY SC BUT ALSO LENGTH, SO NEED TO APPLY TWICE TO OBTAIN BOTH MATRICES??
cd ${out_dir}/tck
# per cada track i ROI

# we should get list of files before entering loop so that it does not
# interfere with created files

create_tracks () {
    ## put everythin inside the loop on a function, and use sem
    filename=$1
    out_dir=$2                            
    fname=${filename%.*}
    a=${fname#*--}
    ROI1=${a%-*}
    ROI2=${a#*-}
    file_size=$(tckstats ${fname}.tck -quiet| tail -n 1| awk '{print $6}');
    file_size=${file_size%.*}
    # if no connection, remove
    if [[ "$file_size" == "" ]]; then
        echo "empty $fname"
        rm -f ${fname}.tck
    # if it is less than 5, also remove
    elif [[ "${file_size}" -lt "5" ]]; then
        echo "less than 5 FC $fname ${file_size}"
        rm -f ${fname}.tck
    # and if it is the same roi, ignore
    elif [ $ROI1 == $ROI2 ] ; then
        echo "equal $ROI1 = $ROI2"
        rm -f ${fname}.tck
    else
        echo "do $ROI1 $ROI2"
        mkdir ${fname}/
        # anat2diff is t1 in diff space
        tckmap ${fname}.tck -template ${out_dir}/anat2diff.nii.gz ${fname}/${fname}.nii.gz 
        # max_int is ?
        max_int=$(fslstats ${fname}/${fname}.nii.gz -R | tail -n 1| awk '{print $2}');
        # Normalization and binarize
        fslmaths ${fname}/${fname} -div $max_int -thr 0.01 -bin ${fname}/${fname}_bin
        # cluster the normalized and binarized image
        cluster -i ${fname}/${fname}_bin -t 1 -o ${fname}/cluster_${fname}_bin
        # get max of clusters
        max_cluster=$(fslstats ${fname}/cluster_${fname}_bin.nii.gz -R | tail -n 1| awk '{print $2}');
        # select only max cluster
        fslmaths ${fname}/cluster_${fname}_bin -thr $max_cluster -bin ${fname}/cluster_${fname}_bin
        # mask excluding the selected region
        # exactament quina màscara és? la mascara del cervell a espai diff?
        fslmaths ${fname}/cluster_${fname}_bin -sub ${out_dir}/dwi_ec_unbiased_mask.nii.gz -abs -bin ${fname}/exclude_${fname}_bin
        # dont understand this step
        fslmaths ${fname}/exclude_${fname}_bin -add ${out_dir}/nodes2diff_bin -bin -sub ${out_dir}/nodes2diff_bin ${fname}/exclude_${fname}_bin
        # select only tracks that explcude that region
        tckedit ${fname}.tck -exclude ${fname}/exclude_${fname}_bin.nii.gz ${fname}/${fname}_tmp.tck
        rm ${fname}/${fname}.nii.gz
        rm ${fname}/cluster_${fname}_bin.nii.gz
        # map that to template again
        tckmap ${fname}/${fname}_tmp.tck -template ${out_dir}/anat2diff.nii.gz ${fname}/${fname}.nii.gz
        # erosion + dilation of the mask
        fslmaths ${fname}/${fname}.nii.gz -bin -kernel 2D -ero -dilM -bin ${fname}/include_${fname}_bin
        # cluster again
        cluster -i ${fname}/include_${fname}_bin -t 1 -o ${fname}/cluster_${fname}_bin
        # find maximum cluster
        max_cluster2=$(fslstats ${fname}/cluster_${fname}_bin.nii.gz -R | tail -n 1| awk '{print $2}');
        # select it
        fslmaths ${fname}/cluster_${fname}_bin -thr $max_cluster2 -bin ${fname}/include_${fname}_bin
        # apply 3D dilation to the mask and adding the two rois
        fslmaths ${fname}/include_${fname}_bin -add ${out_dir}/nodes/${ROI1}.nii.gz -add ${out_dir}/nodes/${ROI2}.nii.gz \
        -kernel 3D -dilM -bin ${fname}/include_${fname}_bin
        # mask the temporal track defined before 
        tckedit ${fname}.tck -mask ${fname}/include_${fname}_bin.nii.gz ${fname}/${fname}_tmp1.tck
        # dilate both rois
        fslmaths ${out_dir}/nodes/${ROI1} -kernel 3D -dilM -bin ${fname}/${ROI1}
        fslmaths ${out_dir}/nodes/${ROI2} -kernel 3D -dilM -bin ${fname}/${ROI2}
        # exclude the not selected  tracks and include the two ROIs
        tckedit ${fname}/${fname}_tmp1.tck -exclude ${fname}/exclude_${fname}_bin.nii.gz -include ${fname}/${ROI1}.nii.gz -include ${fname}/${ROI2}.nii.gz ${fname}_corr.tck
        # map tck to a nii gz
        # the template would be the last image generated by the preprocessing no?
        tckmap ${fname}_corr.tck -template ${out_dir}/dwi_ec_unbiased.nii.gz ${fname}/${fname}_corr.nii.gz

        # remove all the temporal files
        # all those temporal files should be on a separate directory, temporal
        rm -f ${fname}/${ROI1}.nii.gz
        rm -f ${fname}/${ROI2}.nii.gz
        rm -f ${fname}/${fname}_tmp1.tck
        rm -f ${fname}/${fname}_corr.nii.gz
        rm -f ${fname}/${fname}.nii.gz
        rm -f ${fname}/${fname}_bin.nii.gz
        rm -f ${fname}/cluster_${fname}_bin.nii.gz
        rm -f ${fname}/exclude_${fname}_bin.nii.gz
        rm -f ${fname}/${fname}_tmp.tck
        rm -f ${fname}/include_${fname}_bin.nii.gz
        # and remove it afterwards
        rmdir ${fname}/
    fi
}

export -f create_tracks

yourfilenames=`ls *.tck`
echo "arriba al loop"

# do not use the parallelization if we are parallelizing subjects
for filename in $yourfilenames; do
    echo "Create tracks for $filename"
    sem --jobs 20 create_tracks $filename $out_dir
    # create_tracks $filename $out_dir
done
sem --wait

# remove previous
rm -rf ${out_dir}/list_tmp.txt
rm -rf ${out_dir}/list.txt

cd ${out_dir}/tck
for filename in *_corr.tck;do
    # save into list tmp
    echo "$filename" >> ${out_dir}/list_tmp.txt
    fname=${filename%.*}
    tck_file=${fname%_*}
    rm ${tck_file}.tck
done

python -c "import sys; print('\n'.join(' '.join(c) for c in zip(*(l.split() for l in sys.stdin.readlines() if l.strip()))))" < ${out_dir}/list_tmp.txt > ${out_dir}/list.txt
read list <${out_dir}/list.txt

# save into tck file
tckedit $list ${out_dir}/brain_track_AEC.tck

### USE SIFT
tcksift2 ${out_dir}/brain_track_AEC.tck \
${out_dir}/wmfod.mif -act ${out_dir}/5tt2diff.nii \
${out_dir}/brain_track.txt -force -nthreads 6

cd $subj_path

tck2connectome -symmetric -zero_diagonal ${out_dir}/brain_track_AEC.tck \
${out_dir}/nodes2diff.nii.gz ${out_dir}/connectome_weights.csv -tck_weights_in ${out_dir}/brain_track.txt \
-assignment_radial_search $size_thr -force -nthreads 6

tck2connectome -symmetric -zero_diagonal ${out_dir}/brain_track_AEC.tck \
${out_dir}/nodes2diff.nii.gz ${out_dir}/connectome_lengths.csv -tck_weights_in ${out_dir}/brain_track.txt \
-stat_edge mean -scale_length -assignment_radial_search $size_thr -force -nthreads 6

# remove brain_track.tck and folder tck/
rm -rf ${out_dir}/brain_track.tck
rm -rf ${out_dir}/tck/