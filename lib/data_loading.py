"""
Auxiliary functions to load data from datasets.

Depending on the type of the data organization of every dataset.

Mainly two types: BIDS and NO BIDS.
"""

import os
import json
import glob

def load_data(subj_dir, subj_name, type_dir="BIDS"):
    """
    From a specific subject directory, return a dictionary
    with paths of all the image files and information from json (or hardcoded),
    depending on the type.

    Right now only two types:
    - BIDS: all data is organized in the BIDS format (MAINZ)
    - BIDS_MILAN: data organized in BIDS format (MILAN)
    - CLINIC: all data organized as in the clinic dataset.
    """
    d = {} # dictionary where all will be stored

    if type_dir == "MILAN":
        d["T1w"] = glob.glob(f'{subj_dir}/anat/*_MPR_*.nii')[0]

        if len(glob.glob(f'{subj_dir}/anat/FLAIR2T1.nii.gz')):
            d["FLAIR"] = glob.glob(f'{subj_dir}/anat/FLAIR2T1.nii.gz')[0]
            d["Lesions"] = f'{subj_dir}/anat/FLAIR_LesMask2t1.nii.gz' # no need to run it
        else:
            d["FLAIR"] = None
            d["Lesions"] = None

        # DWI
        d["DWI"] = glob.glob(f'{subj_dir}/dwi/*_DW*.nii')[0]
        d["bvec"] = glob.glob(f'{subj_dir}/dwi/*_DW*.bvec')[0]
        d["bval"] = glob.glob(f'{subj_dir}/dwi/*_DW*.bval')[0]
        d["dwi_json"] = glob.glob(f'{subj_dir}/dwi/*_DW*.json')[0] # always check json for each new dataset to make sure format is same

        # DWI2 for EPI distortion correction
        d["DWI2"] = glob.glob(f'{subj_dir}/dwi/*_b0*.nii')[0]
        d["bvec2"] = None
        d["bval2"] = None

        # DWi phase and magnitude for EPI distortion correction
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        # load json and extract values
        with open(d["dwi_json"]) as f:
            dwi_json = json.load(f)

        d["dwell"] = None
        # d["dwell"] = dwi_json["EffectiveEchoSpacing"] # DT (dwell)
        d["TE"] = dwi_json["EchoTime"]* 1000.0 # DeltaTE (echo time difference of the fieldmap sequence), in s

        # not needed right now
        d["readout"] = None
        d["ScanningSequence"] = None

        # fMRI
        d["fMRI"] = glob.glob(f'{subj_dir}/func/*rsfMRI_*.nii')[0]
        d["fMRI_json"] = glob.glob(f'{subj_dir}/func/*rsfMRI_*.json')[0] # always check json for each new dataset to make sure format is same

        with open(d["fMRI_json"]) as f:
            fmri_json = json.load(f)
    
        d["TR"] = fmri_json["RepetitionTime"]*1000 # convert seconds to MS

    if type_dir == "MAINZ":
        # T1
        d["T1w"] = f'{subj_dir}/anat/{subj_name}_T1w.nii'
        d["FLAIR"] = f'{subj_dir}/anat/{subj_name}_FLAIR.nii'

        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it
        else:
            d["Lesions"] = None # need to run it

        # DWI
        d["DWI"] = f'{subj_dir}/dwi/{subj_name}_dwi.nii'
        d["bvec"] = f'{subj_dir}/dwi/{subj_name}_dwi.bvec'
        d["bval"] = f'{subj_dir}/dwi/{subj_name}_dwi.bval'
        d["dwi_json"] = f'{subj_dir}/dwi/{subj_name}_dwi.json' # always check json for each new dataset to make sure format is same

        # DWI2 for EPI distortion correction
        d["DWI2"] = None
        d["bvec2"] = None
        d["bval2"] = None

        # DWi phase and magnitude
        # not available!
        # TODO: availability checking?
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        # load json and extract values
        with open(d["dwi_json"]) as f:
            dwi_json = json.load(f)
        d["dwell"] = dwi_json["EffectiveEchoSpacing"] # DT (dwell)
        d["TE"] = dwi_json["EchoTime"] # DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = dwi_json["TotalReadoutTime"]
        d["ScanningSequence"] = dwi_json["ScanningSequence"] # order of scanning sequence
        # d["PhaseEncodingDir"] = dwi_json["PhaseEncodingDir"] # Phase encoding direction

        # fMRI
        d["fMRI"] = f'{subj_dir}/func/{subj_name}_bold.nii'
        d["fMRI_json"] = f'{subj_dir}/func/{subj_name}_bold.json' # always check json for each new dataset to make sure format is same

        with open(d["fMRI_json"]) as f:
            fmri_json = json.load(f)
    
        d["TR"] = fmri_json["RepetitionTime"]*1000 # convert seconds to MS

    if type_dir == "NAPLES":
        # very similar to MAINZ, BUT FLAIR IS IN ANOTHER FOLDER
        # T1
        d["T1w"] = f'{subj_dir}/anat/{subj_name}_T1w.nii'
        d["FLAIR"] = f'{subj_dir}/flair/{subj_name}_flair.nii'

        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it again
        else:
            d["Lesions"] = None # need to run it

        # DWI
        d["DWI"] = f'{subj_dir}/dwi/{subj_name}_dwi.nii'
        d["bvec"] = f'{subj_dir}/dwi/{subj_name}_dwi.bvec'
        d["bval"] = f'{subj_dir}/dwi/{subj_name}_dwi.bval'
        d["dwi_json"] = f'{subj_dir}/dwi/{subj_name}_dwi.json' # always check json for each new dataset to make sure format is same

        # DWI2 for EPI distortion correction
        d["DWI2"] = None
        d["bvec2"] = None
        d["bval2"] = None

        # DWi phase and magnitude
        # not available!
        # TODO: availability checking?
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        # load json and extract values
        with open(d["dwi_json"]) as f:
            dwi_json = json.load(f)
        d["dwell"] = dwi_json["EffectiveEchoSpacing"] # DT (dwell)
        d["TE"] = dwi_json["EchoTime"] # DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = dwi_json["TotalReadoutTime"]
        d["ScanningSequence"] = dwi_json["ScanningSequence"] # order of scanning sequence
        # d["PhaseEncodingDir"] = dwi_json["PhaseEncodingDir"] # Phase encoding direction

        # fMRI
        d["fMRI"] = f'{subj_dir}/func/{subj_name}_bold.nii'
        d["fMRI_json"] = f'{subj_dir}/func/{subj_name}_bold.json' # always check json for each new dataset to make sure format is same

        with open(d["fMRI_json"]) as f:
            fmri_json = json.load(f)
    
        d["TR"] = fmri_json["RepetitionTime"]*1000 # convert seconds to MS

    elif type_dir == "CLINIC":
        # T1
        d["T1w"] = f'{subj_dir}/r{subj_name}_T1_00.nii.gz'
        d["FLAIR"] = f'{subj_dir}/r{subj_name}_FLAIR_00.nii.gz'
        # d["Lesions"] = f'{subj_dir}/r{subj_name}_ROI_00.nii.gz' # need to run it

        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it
        else:
            d["Lesions"] = None # need to run it

        # DWI
        d["DWI"] = f'{subj_dir}/r{subj_name}_DWI_00.nii.gz'
        d["bvec"] = f'{subj_dir}/r{subj_name}_DWI_00.bvec'
        d["bval"] = f'{subj_dir}/r{subj_name}_DWI_00.bval'
        d["dwi_json"] = None # always check json for each new dataset to make sure format is same

        # DWI2 for EPI distortion correction
        d["DWI2"] = None
        d["bvec2"] = None
        d["bval2"] = None

        # DWi phase and magnitude
        d["DWI_ph"] = f'{subj_dir}/r{subj_name}_GFM_ph_00.nii.gz'
        d["DWI_mag"] = f'{subj_dir}/r{subj_name}_GFM_mag_00.nii.gz'

        # values
        d["dwell"] = 0.485 # DT (dwell)
        d["TE"] = 103 # DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = None
        d["ScanningSequence"] = None # order of scanning sequence
        d["PhaseEncodingDir"] = None # Phase encoding direction

        # fMRI
        d["fMRI"] = f'{subj_dir}/r{subj_name}_RESTING_00.nii.gz'
        d["fMRI_json"] = None # always check json for each new dataset to make sure format is same
        d["TR"] = 2000 # convert seconds to MS

    if type_dir == "OSLO":
        # very similar to MAINZ, BUT FLAIR IS IN ANOTHER FOLDER
        # T1

        # subj dir need to add the ses
        # subj_dir = glob.glob(f'{subj_dir}/*/')[0]

        d["T1w"] = glob.glob(f'{subj_dir}/*/anat/{subj_name}*_T1w.nii.gz')[0]
        d["FLAIR"] = glob.glob(f'{subj_dir}/*/anat/{subj_name}*_FLAIR.nii.gz')[0]

        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it
        else:
            d["Lesions"] = None # need to run it

        # DWI
        d["DWI"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*AP_dwi.nii.gz')[0]
        d["bvec"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*AP_dwi.bvec')[0]
        d["bval"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*AP_dwi.bval')[0]
        d["dwi_json"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*AP_dwi.json')[0] # always check json for each new dataset to make sure format is same

        # DWI2 for EPI distortion correction
        d["DWI2"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.nii.gz')[0]
        d["bvec2"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.bvec')[0]
        d["bval2"] = glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.bval')[0]

        # DWi phase and magnitude
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        # load json and extract values
        with open(d["dwi_json"]) as f:
            dwi_json = json.load(f)
        d["dwell"] = dwi_json["EffectiveEchoSpacing"] # DT (dwell)
        d["TE"] = dwi_json["EchoTime"] # DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = dwi_json["TotalReadoutTime"]
        d["ScanningSequence"] = dwi_json["ScanningSequence"] # order of scanning sequence
        # d["PhaseEncodingDir"] = dwi_json["PhaseEncodingDir"] # Phase encoding direction

        # fMRI
        d["fMRI"] = glob.glob(f'{subj_dir}/*/func/{subj_name}*_bold.nii.gz')[0]
        d["fMRI_json"] = glob.glob(f'{subj_dir}/*/func/{subj_name}*_bold.json')[0] # always check json for each new dataset to make sure format is same

        with open(d["fMRI_json"]) as f:
            fmri_json = json.load(f)
    
        d["TR"] = fmri_json["RepetitionTime"]*1000 # convert seconds to MS

    if type_dir == "AMSTERDAM":
        d["T1w"] = glob.glob(f'{subj_dir}/*_sienax/I.nii.gz')[0]
        d["FLAIR"] = f'{subj_dir}/flair.nii.gz'
        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it
        else:
            d["Lesions"] = None # need to run it

        # DWI
        d["DWI"] = f'{subj_dir}/raw.nii.gz'
        d["bvec"] = f'{subj_dir}/bvecs'
        d["bval"] = f'{subj_dir}/bvals'
        d["dwi_json"] = None

        # DWI2 for EPI distortion correction
        d["DWI2"] = None
        d["bvec2"] = None
        d["bval2"] = None

        # DWi phase and magnitude
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        d["dwell"] = None # DT (dwell)
        d["TE"] = 91 # ms DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = None
        d["ScanningSequence"] = None # order of scanning sequence

        # fMRI
        d["fMRI"] = f'{subj_dir}/fmri.nii.gz'
        d["fMRI_json"] = None
    
        d["TR"] = 2200


    if type_dir == "LONDON":
        
        d["T1w"] = glob.glob(f'{subj_dir}/*/anat/*_t1.nii.gz')[0]
        d["FLAIR"] = glob.glob(f'{subj_dir}/*/anat/*_flair.nii.gz')[0]

        if len(glob.glob(f'{subj_dir}/{subj_name}_ROI*')) > 0:
            d["Lesions"] = glob.glob(f'{subj_dir}/{subj_name}_ROI*')[0] # no need to run it
        else:
            d["Lesions"] = None # need to run it

        # DWI
        # Very strange, very weird
        try:
            d["DWI"] = glob.glob(f'{subj_dir}/*/dwi/final_dwi.nii.gz')[0]
            d["bvec"] = glob.glob(f'{subj_dir}/*/dwi/final_dwi.bvec')[0]
            d["bval"] = glob.glob(f'{subj_dir}/*/dwi/final_dwi.bval')[0]
        except IndexError:
            d["DWI"] = glob.glob(f'{subj_dir}/*/dwi/*_dwi.nii.gz')[0]
            d["bvec"] = glob.glob(f'{subj_dir}/*/dwi/*_dwi.bvec')[0]
            d["bval"] = glob.glob(f'{subj_dir}/*/dwi/*_dwi.bval')[0]


        if len(glob.glob(f'{subj_dir}/*/dwi/*_dwi.json')) > 0:
            d["dwi_json"] = glob.glob(f'{subj_dir}/*/dwi/*_dwi.json')[0] # always check json for each new dataset to make sure format is same
        else:
            d["dwi_json"] = glob.glob(f'{subj_dir}/*/dwi/*_dwi_b300.json')[0] # always check json for each new dataset to make sure format is same



        if len(glob.glob(f'{subj_dir}/*/dwi/*_b0_rev.nii.gz')) > 0:
            d["DWI2"] = glob.glob(f'{subj_dir}/*/dwi/*_b0_rev.nii.gz')[0]
        # DWI2 for EPI distortion correction
        else:
            d["DWI2"] = None #glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.nii.gz')[0]
        
        d["bvec2"] = None #glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.bvec')[0]
        d["bval2"] = None #glob.glob(f'{subj_dir}/*/dwi/{subj_name}*PA_dwi.bval')[0]

        # DWi phase and magnitude
        d["DWI_ph"] = None
        d["DWI_mag"] = None

        # load json and extract values
        with open(d["dwi_json"]) as f:
            dwi_json = json.load(f)
        d["dwell"] = dwi_json["EstimatedEffectiveEchoSpacing"] # DT (dwell)
        d["TE"] = dwi_json["EchoTime"] # DeltaTE (echo time difference of the fieldmap sequence), normally 2.46ms in SIEMENS
        d["readout"] = dwi_json["EstimatedTotalReadoutTime"]
        d["ScanningSequence"] = dwi_json["ScanningSequence"] # order of scanning sequence
        # d["PhaseEncodingDir"] = dwi_json["PhaseEncodingDir"] # Phase encoding direction

        # fMRI
        d["fMRI"] = glob.glob(f'{subj_dir}/*/fmri/*_rsfmri.nii.gz')[0]
        d["fMRI_json"] = glob.glob(f'{subj_dir}/*/fmri/*_rsfmri.json')[0] # always check json for each new dataset to make sure format is same

        with open(d["fMRI_json"]) as f:
            fmri_json = json.load(f)
    
        d["TR"] = fmri_json["RepetitionTime"]*1000 # convert seconds to MS


    return d