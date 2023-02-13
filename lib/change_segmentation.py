"""
Python script to change the segmentation numbers to lower numbers 
(sequential values) and removing segmentations that are not
relevant
"""
import nibabel as nib
import os
import sys
import numpy as np

# REMOVED:
# Cortical white matter, cerebellar white matter,
# ventricles, BrainStem, CSF
# VentralDC out
# ChoroidPlexus out

# dictionary of labels, our label: name
# follow the ordre proposed by FastSurfer, but
# ignore the labels that are not GM
# this dictionary is absurd, because we can later
# map automatically

### REMOVE THE CEREBELLUM CORTEX FOR TRUE PARCELLATION


def new_labels():
    """
    ¿static? function that returns two dictionaries:
    labels_name_dict, which the actual dictionary of the labels
                      with their original number and name

    fs_dict, with the key being the new number and the value being
             the corresponding key of the other dictionary
    """

    labels_name_dict = {
        # "8": "L_CerebellumCortex", # NOT INCLUDED A AAL
        "10": "L_Thalamus",
        "11": "L_Caudate",
        "12": "L_Putamen",
        "13": "L_Pallidum",
        "17": "L_Hippocampus",
        "18": "L_Amygdala",
        "26": "L_Accumbens",  # NOT INCLUDED A AAL
        # "18": "L_ChoroidPlexus",
        # "47": "R_CerebellumCortex", # NOT INCLUDED A AAL
        "49": "R_Thalamus",
        "50": "R_Caudate",
        "51": "R_Putamen",
        "52": "R_Pallidum",
        "53": "R_Hippocampus",
        "54": "R_Amygdala",
        "58": "R_Accumbens",  # NOT INCLUDED A AAL
        # "32": "R_ChoroidPlexus",
        "1002": "L_CaudalAnteriorCingulate",
        "1003": "L_CaudalMiddleFrontal",
        "1005": "L_Cuneus",
        "1006": "L_Entorhinal",
        "1007": "L_Fusiform",
        "1008": "L_InferiorParietal",
        "1009": "L_InferiorTemporal",
        "1010": "L_Isthmuscingulate",
        "1011": "L_LateralOccipital",
        "1012": "L_LateralOrbitoFrontal",
        "1013": "L_Lingual",
        "1014": "L_MedialOrbitoFrontal",
        "1015": "L_MiddleTemporal",
        "1016": "L_ParaHippocampal",
        "1017": "L_ParaCentral",
        "1018": "L_ParsOpercularis",
        "1019": "L_ParsOrbitalis",
        "1020": "L_ParsTriangularis",
        "1021": "L_PeriAlcarine",
        "1022": "L_PostCentral",
        "1023": "L_PosteriorCingulate",
        "1024": "L_PreCentral",
        "1025": "L_Precuneus",
        "1026": "L_RostralAnteriorCingulate",
        "1027": "L_RostralMiddleFrontal",
        "1028": "L_SuperiorFrontal",
        "1029": "L_SuperiorParietal",
        "1030": "L_SuperiorTemporal",
        "1031": "L_SupraMarginal",
        "1034": "L_TraverseTemporal",
        "1035": "L_Insula",
        "2002": "R_CaudalAnteriorCingulate",
        "2003": "R_CaudalMiddleFrontal",
        "2005": "R_Cuneus",
        "2006": "R_Entorhinal",
        "2007": "R_Fusiform",
        "2008": "R_InferiorParietal",
        "2009": "R_InferiorTemporal",
        "2010": "R_Isthmuscingulate",
        "2011": "R_LateralOccipital",
        "2012": "R_LateralOrbitoFrontal",
        "2013": "R_Lingual",
        "2014": "R_MedialOrbitoFrontal",
        "2015": "R_MiddleTemporal",
        "2016": "R_ParaHippocampal",
        "2017": "R_ParaCentral",
        "2018": "R_ParsOpercularis",
        "2019": "R_ParsOrbitalis",
        "2020": "R_ParsTriangularis",
        "2021": "R_PeriAlcarine",
        "2022": "R_PostCentral",
        "2023": "R_PosteriorCingulate",
        "2024": "R_PreCentral",
        "2025": "R_Precuneus",
        "2026": "R_RostralAnteriorCingulate",
        "2027": "R_RostralMiddleFrontal",
        "2028": "R_SuperiorFrontal",
        "2029": "R_SuperiorParietal",
        "2030": "R_SuperiorTemporal",
        "2031": "R_SupraMarginal",
        "2034": "R_TraverseTemporal",
        "2035": "R_Insula",
    }

    fs_dict = {}
    i = 1
    # create new dictionary fs_label: our label (ordered)
    for key in sorted(labels_name_dict.keys(), key=int):
        fs_dict[key] = i
        i += 1

    return labels_name_dict, fs_dict


def new_segmentation(seg):
    """
    Function to update the segmentation obtained by FastSurfer to
    have sequenced values.
    """
    # load the image
    seg_nii = nib.load(seg)

    labels_name_dict, fs_dict = new_labels()

    # create empty numpy
    new_data = np.zeros(seg_nii.shape, dtype=int)

    # get original data
    seg_nii_data = seg_nii.get_fdata().astype(int)

    # for each value in the dict, fill the empty numpy
    for key in fs_dict.keys():
        mask_node = seg_nii_data == int(key)
        new_data[mask_node] = fs_dict[key]

    # save the values to a new image
    new_nii = nib.Nifti1Image(new_data, seg_nii.affine, seg_nii.header)
    nib.save(new_nii, seg.replace(".nii.gz", "") + "_newSeg.nii.gz")


if __name__ == "__main__":

    # inputs
    # first input should be the segmentation
    try:
        seg = sys.argv[1]
    except:
        print("No file indicated")
        sys.exit()

    new_segmentation(seg)
