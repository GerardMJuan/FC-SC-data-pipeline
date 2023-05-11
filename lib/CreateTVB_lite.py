"""
Consolidate all processed information.

Just copy over the matrices to directory results, in the appropiate name
Also save the region names, which is not needed for the algorithm but is
handy to have.

Adapted from CreateTVB.m to python. Original script by:
% Authors: Michael Schirner, Simon Rothmeier, Petra Ritter
% BrainModes Research Group (head: P. Ritter)
% Charité University Medicine Berlin & Max Planck Institute Leipzig, Germany
% Correspondence: petra.ritter@charite.de

"""

import numpy as np
import os
import shutil
import zipfile
from lib.change_segmentation import new_labels
from nilearn.plotting import find_parcellation_cut_coords
from nilearn.image import load_img

def CreateTVB(subjID, subj_dir, out_dir):
    """
    Main function to create the zip input to the TVB framework.
    We assume that all the previous preprocessing steps have been done
    Contents of the zip described in: docs.thevirtualbrain.org/manuals/UserGuide/DataExchange.html
    Input:
        subjID: ID of the subject
        subj_dir: Directory of the subject
        out_dir: Output directory
    Output:
        no output, but {subjID}.zip created in output_dir, containing all the necessary files
    """

    # create output dir if doesnt exist
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # load the SC matrices
    SC_path_weight = f'{subj_dir}/dt_proc/connectome_weights.csv'
    SC_path_length = f'{subj_dir}/dt_proc/connectome_lengths.csv'

    SC_weight = np.loadtxt(SC_path_weight, delimiter=',')
    SC_length = np.loadtxt(SC_path_length, delimiter=',')

    # try different normalization for SC_weight
    # SC_weight_norm1 = SC_weight / max(sum(SC_weight))
    results_SC_norm = SC_weight / max(np.sum(SC_weight, axis=0))

    SC_weight_norm1 = (SC_weight - np.amin(SC_weight)) / (np.amax(SC_weight) - np.amin(SC_weight))
    SC_weight_norm1 = SC_weight_norm1 * 0.2
    # start writing the files

    ### 1: Weights
    # check if encoding is correct
    # do we need to normalize?
    # check for zeros?
    np.savetxt(f'{out_dir}/{subjID}_SC_weights.txt', SC_weight_norm1, encoding='ascii')
    np.savetxt(f'{out_dir}/{subjID}_SC_weights_nonorm.txt', SC_weight, encoding='ascii')

    ### 2: Tract lengths
    np.savetxt(f'{out_dir}/{subjID}_SC_distances.txt', SC_length, encoding='ascii')

    # save again with the appropiate name for the connectivity
    np.savetxt(f'{out_dir}/weights.txt', SC_weight_norm1, encoding='ascii')
    np.savetxt(f'{out_dir}/tract_lengths.txt', SC_length, encoding='ascii')

    ### 2: Region centers
    # take the mean of every region
    # do the centers need to be existing vertices? NO

    # load segmentation (new)
    aseg_aparc = load_img(f'{subj_dir}/recon_all/mri/aparc.DKTatlas+aseg_newSeg.nii.gz')
    labels_name_dict, fs_dict = new_labels()
    new_labels_dict = {fs_dict[k]: v for k, v in labels_name_dict.items()}

    # use find_parcellation_cut_coords?
    centers = find_parcellation_cut_coords(aseg_aparc)
    # more complex than that 
    with open(f'{out_dir}/centres.txt', 'w') as f:
        # Write each line in the correct format
        for (i, i_c) in enumerate(centers):
            f.write(f'{new_labels_dict[i+1]} {i_c[0]} {i_c[1]} {i_c[2]}\n')


    ## SAVE WEIGHTS AND TRACT ON CONNECTIVITY.ZIP
    ## FINAL: Create ZIP
    if os.path.isfile(f'{out_dir}/Connectivity.zip'): os.remove(f'{out_dir}/Connectivity.zip')
    files_to_compress = ['weights.txt', 'tract_lengths.txt', 'centres.txt']
    with zipfile.ZipFile(f'{out_dir}/Connectivity.zip', 'w') as myzip:
        for f in files_to_compress:
            myzip.write(f'{out_dir}/{f}', arcname=f)


    # copy fmri matrix
    # copy both and we decide on runtime which one is the best option
    shutil.copy(f'{subj_dir}/fmri_proc_dti/r_matrix.csv', f'{out_dir}/')
    shutil.copy(f'{subj_dir}/fmri_proc_dti/zr_matrix.csv', f'{out_dir}/')
    # also need to copy the information about the BOLD signal so that we can compute the metastability later
    shutil.copy(f'{subj_dir}/fmri_proc_dti/corrlabel_ts.txt', f'{out_dir}/')

    
if __name__ == "__main__":
    subjID = 
    subj_dir = 
    out_dir = 

    CreateTVB(subjID, subj_dir, out_dir)
