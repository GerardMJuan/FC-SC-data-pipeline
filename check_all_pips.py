"""
Script that jointly checks for all the datasets that we have.

This builds over all the datasets and creates a csv with the progress
of the preprocessing for all of them.
"""

import pandas as pd
import numpy as np
import datetime
import os

out_dir = "
total_csv = f"{out_dir}/data_total.csv"

df_total = pd.read_csv(total_csv)

subj_list = []
centre_list = []
completion_list = [[] for i in range(6)]

# iterate over subjects, 
for row in df_total.itertuples():

    # subject dir
    subID = row.SubjID

    centre_list.append(row.CENTER)

    subj_list.append(subID)

    out_dir_subject = f'{out_dir}/{row.CENTER}_Post/{subID}'

    if not os.path.exists(out_dir_subject):
        os.makedirs(out_dir_subject)
        
    #1 Fastsurfer
    fastsurfer_done = os.path.isfile(f'{out_dir_subject}/recon_all/scripts/recon-all.done') and os.path.isfile(f'{out_dir_subject}/recon_all/scripts/recon-surf.done')
    completion_list[0].append(fastsurfer_done)

    #1.5 WM Lesion Segmentation
    # NO INCLUSION BECAUSE A LOT OF VARIABILITY AND ISSUES (HEALTHIES, OHTERS) - JUST DO MANUALLY
    # lst_done = os.path.isfile(f'{base_data_dir}/{subID}/r{subID}_ROI_00.nii.gz') or os.path.isfile(f'{base_data_dir}/{subID}/{subID}_ROI.nii.gz')
    # completion_list[1].append(lst_done)

    #2 DWI preprocessing
    dt_done = os.path.isfile(f'{out_dir_subject}/dt_proc/connectome_weights.csv')
    completion_list[2].append(dt_done)

    #3 compute SC
    sc_done = os.path.isfile(f'{out_dir_subject}/dt_proc/connectome_weights.csv')
    completion_list[3].append(sc_done)

    #4 fMRI
    fmri_done = os.path.isfile(f'{out_dir_subject}/fmri_proc_dti/r_matrix.nii.gz')
    completion_list[4].append(fmri_done)

    #5 convert to TVB
    # tvb lite
    tvb_done = os.path.isfile(f'{out_dir_subject}/results/{subID}_SC_distances.txt') and os.path.isfile(f'{out_dir_subject}/results/{subID}_SC_weights.txt') and os.path.isfile(f'{out_dir_subject}/results/r_matrix.csv') and os.path.isfile(f'{out_dir_subject}/results/Connectivity.zip')
    completion_list[5].append(tvb_done)

# create dictionary
dict_check = {
    "id": subj_list,
    "CENTER": centre_list,
    "fastsurfer": completion_list[0],
    "DWI_preproc": completion_list[2],
    "agg_SC": completion_list[3],
    "fMRI": completion_list[4],
    "toTVB": completion_list[5]
}

# save csv tofile
pd_results = pd.DataFrame(dict_check)
pd_results.to_csv(f"{out_dir}/pipeline.csv", index=False)