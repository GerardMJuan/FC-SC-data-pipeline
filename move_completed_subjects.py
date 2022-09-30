"""
Small script that moves the final results of the subjects
to a folder in the Nascarm01
For safekeeping and backup reasons.
"""

import click
import shutil
import os
import pandas as pd
import numpy as np

@click.command(help="Move the results folder to create a backup on the desired folder .")
@click.option("--pip_csv", type=click.STRING, help="csv with the completed pipeline")
@click.option("--out_dir", type=click.STRING, help="Directory where we will store the results. Each subject would have a subdirectory")
@click.argument("ind_dir")
def move_completed_subjects(ind_dir, pip_csv, out_dir):

    df_pipeline = pd.read_csv(pip_csv)
    for row in df_pipeline.itertuples():
        subID = row.id
        type_dir = row.CENTER

        if type_dir != "LONDON": continue
        # if type_dir != "CLINIC": continue
        subj_dir_id = f'{ind_dir}/{type_dir}_Post/{subID}'

        # store only subjects that have been processed
        if row.toTVB:
            out_dir_subj = f'{out_dir}/{type_dir}_{subID}'

            # create subject if it does not exist
            if not os.path.exists(f'{out_dir_subj}/results/'):
                os.makedirs(f'{out_dir_subj}/results/')

            # copy connectivity.zip, weights, tracts, z_matrix and zr_matrix
            shutil.copy2(f'{subj_dir_id}/results/Connectivity.zip', f'{out_dir_subj}/results/')
            shutil.copy2(f'{subj_dir_id}/results/{subID}_SC_distances.txt', f'{out_dir_subj}/results/{type_dir}_{subID}_SC_distances.txt')
            shutil.copy2(f'{subj_dir_id}/results/{subID}_SC_weights.txt', f'{out_dir_subj}/results/{type_dir}_{subID}_SC_weights.txt')
            shutil.copy2(f'{subj_dir_id}/fmri_proc_dti/r_matrix.csv', f'{out_dir_subj}/results/')
            shutil.copy2(f'{subj_dir_id}/fmri_proc_dti/zr_matrix.csv', f'{out_dir_subj}/results/')
            shutil.copy2(f'{subj_dir_id}/fmri_proc_dti/corrlabel_ts.txt', f'{out_dir_subj}/results/')

# python move_completed_subjects.py /home/extop/GERARD/DATA/MAGNIMS2021 --pip_csv /home/extop/GERARD/DATA/MAGNIMS2021/pipeline.csv --out_dir /mnt/Bessel/Gproj/Gerard_DATA/MAGNIMS2021/output_fmri_dti

if __name__ == "__main__":
    # those parameters have to be entered from outside
    move_completed_subjects()