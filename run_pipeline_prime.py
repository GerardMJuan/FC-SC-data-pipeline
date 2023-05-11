"""
New version of run pipeline. Changes:

- Works with the unified csv. 
- Can run over subsets of subjects indicated by a txt file
- Can run parallel over subjects, limiting intra subject threading
"""

import os
import pandas as pd
from contextlib import redirect_stdout, redirect_stderr
import subprocess
import shutil
import argparse
from lib.change_segmentation import new_segmentation
from lib.make_stc import make_fsl, make_milan
from lib.CreateTVB_lite import CreateTVB
from lib.data_loading import load_data
import datetime
import numpy as np
from joblib import Parallel, delayed


def run_pipeline(
    row, df_pip_status, out_dir, subj_list, base_data_dir, fs, lst, dt, tck, tvb
):
    """
    Function that implements the pipeline, so that
    this thing can be parallelized.

    Only apply to the steps that are not done.
    """

    # subject dir
    subID = row.SubjID
    type_dir = row.CENTER

    # hardcoded because yes
    working_dir_raw = ""

    ### sub-MS0186 DOESNT WORK
    if subID == "FIS_083":
        return 0
    if subID == "FIS_121":
        return 0
    if subID == "sub-MS0186":
        return 0
    if subID == "sub-0010" and type_dir == "MAINZ":
        return 0
    if subID == "sub-0026" and type_dir == "MAINZ":
        return 0
    if subID == "sub-0010" and type_dir == "MAINZ":
        return 0

    # information about pipeline steps
    fastsurfer_status = df_pip_status[
        (df_pip_status.id == subID) & (df_pip_status.CENTER == type_dir)
    ]["fastsurfer"].bool()
    dt_status = df_pip_status[
        (df_pip_status.id == subID) & (df_pip_status.CENTER == type_dir)
    ]["DWI_preproc"].bool()
    sc_status = df_pip_status[
        (df_pip_status.id == subID) & (df_pip_status.CENTER == type_dir)
    ]["agg_SC"].bool()
    tvb_status = df_pip_status[
        (df_pip_status.id == subID) & (df_pip_status.CENTER == type_dir)
    ]["toTVB"].bool()

    # only do steps if are not done AND we have the flag to do that step
    # we assume that all previous steps will run
    do_fs = (not fastsurfer_status) and fs
    do_dt = (not dt_status) and dt
    do_tck = (not sc_status) and tck
    do_tvb = (not tvb_status) and tvb and sc_status
    do_lst = lst

    # if no task is assigned for this subject, then don't do anything
    if not (do_fs or do_dt or do_tck or do_tvb or do_lst):
        return 0

    # make directory
    out_dir_subject = f"{out_dir}/{type_dir}_Post/{subID}"

    # copy the raw data to local
    os.system(f"cp -R {base_data_dir}/{type_dir}/{subID} {working_dir_raw}/")

    # load the data
    # here we need to do a try because if it fails (and we assume that the function works well)
    # it means that some of the data is missing and it is not worth it to process it
    try:
        d = load_data(f"{working_dir_raw}/{subID}", subID, type_dir)
    except:
        print(f"Problem loading data for subject {subID} from {type_dir}")
        return -1
    # create directory if doesnt exist
    if not os.path.exists(out_dir_subject):
        os.makedirs(out_dir_subject)

    if do_fs:
        output_file = out_dir_subject + "/log_fs.txt"
        print(f"Running FastSurfer for {subID}...")
        with open(output_file, "w") as f:
            cmd = subprocess.Popen(
                f'exec scripts/FastSurfer.sh {subID} {d["T1w"]} {out_dir_subject}',
                shell=True,
                stdout=f,
                stderr=f,
            )
            cmd.wait()

    # check if flair exists, if it doesnt, just don't do it
    if do_lst and os.path.isfile(d["FLAIR"]):
        ### HACK remove directory if exists
        if os.path.exists(f"{out_dir_subject}/lst"):
            os.system(f"rm -rf {out_dir_subject}/lst/")

        output_file = out_dir_subject + "/log_lst.txt"
        print(f"Running LST for {subID}...")
        with open(output_file, "w") as f:
            cmd = subprocess.Popen(
                f'exec scripts/runLST.sh {subID} {d["T1w"]} {d["FLAIR"]} {out_dir_subject} {type_dir}',
                shell=True,
                stdout=f,
                stderr=f,
            )
            cmd.wait()

    if do_dt:
        os.system(f"rm -rf {out_dir_subject}/dt_recon")
        os.system(f"rm -rf {out_dir_subject}/dt_proc")
        os.system(f"rm -rf {out_dir_subject}/dt_recon_lowshell")

        # create directory if doesnt exist
        if not os.path.exists(f"{out_dir_subject}/dt_recon"):
            os.makedirs(f"{out_dir_subject}/dt_recon")

        # create directory if doesnt exist
        if not os.path.exists(f"{out_dir_subject}/dt_proc"):
            os.makedirs(f"{out_dir_subject}/dt_proc")

        output_file = out_dir_subject + "/log_dt.txt"
        print(f"Running DT_recon for {subID}...")
        # redirect all output to file

        with open(output_file, "w") as f:
            cmd = subprocess.Popen(
                f'exec scripts/DT_recon.sh {subID} {out_dir_subject} {d["DWI"]} {d["DWI2"]} {d["bval"]} {d["bvec"]} {d["Lesions"]}\
                                      {type_dir} {d["DWI_ph"]} {d["DWI_mag"]} {d["dwi_json"]} {d["bval2"]} {d["bvec2"]}',
                shell=True,
                stdout=f,
                stderr=f,
            )
            cmd.wait()

    if do_tck:
        output_file = out_dir_subject + "/log_track.txt"
        print(f"Running Tracking for {subID}...")

        # first, create new segmentation
        seg_file = f"{out_dir_subject}/recon_all/mri/aparc.DKTatlas+aseg.nii.gz"

        # RUN the python function in LIB
        try:
            new_segmentation(seg_file)
        except:
            print(f"new segmentation for {subID} failed!")
            return 0
        # redirect all output to file
        with open(output_file, "w") as f:
            cmd = subprocess.Popen(
                f"exec scripts/Tracking.sh {subID} {out_dir_subject}",
                shell=True,
                stdout=f,
                stderr=f,
            )
            cmd.wait()

    if do_tvb:
        print(f"Running TVB for {subID}...")

        # create directory if doesnt exist
        if not os.path.exists(f"{out_dir_subject}/results/results"):
            os.makedirs(f"{out_dir_subject}/results/results")

        output_file = out_dir_subject + "/log_tvb.txt"

        try:
            CreateTVB(subID, out_dir_subject, f"{out_dir_subject}/results/")
        except:
            print(f"CreateTVB for {subID} failed!")
            return 0

    # remove the temporal values
    shutil.rmtree(f"{working_dir_raw}/{subID}")
    print(f"Finished {subID}!")
    return 0


parser = argparse.ArgumentParser()
parser.add_argument(
    "--in_dir",
    type=str,
    required=True,
    help="input dir with subject data, general input dir (MAGNIMS2021",
)
parser.add_argument(
    "--in_csv", type=str, required=True, help="csv with the subject info (general csv)"
)
parser.add_argument(
    "--in_pip",
    type=str,
    required=True,
    help="csv with the information of the current state of the pipeline",
)
parser.add_argument(
    "--out_dir",
    type=str,
    required=True,
    help="A string argument (also general directory)",
)
parser.add_argument("--njobs", type=int, default=1, help="Number of jobs to use")
parser.add_argument(
    "--subj_list", type=str, help="A text file with a list of subjects, one per line"
)
parser.add_argument("-fs", action="store_true")
parser.add_argument("-lst", action="store_true")
parser.add_argument("-dt", action="store_true")
parser.add_argument("-tck", action="store_true")
parser.add_argument("-tvb", action="store_true")

# Parse and print the results
args = parser.parse_args()

# select type of data loading
base_data_dir = args.in_dir
out_dir = args.out_dir

# read the csv
# esta a base dir, copiar
df_connect = pd.read_csv(args.in_csv)
currentDirectory = os.getcwd()

# read the completion csv
df_pip_status = pd.read_csv(args.in_pip)

df_connect_todo = pd.DataFrame(columns=df_connect.columns, dtype=object)

if args.subj_list:
    subj_list = np.genfromtxt(args.subj_list, delimiter=",", dtype="str")
    for s in subj_list:
        # s[0] should be the id, s[1] should be the center
        df_connect_todo = df_connect_todo.append(
            df_connect[(df_connect.SubjID == s[0]) & (df_connect.CENTER == s[1])]
        )  # will select subjects taht we don't have to process
else:
    subj_list = []
    df_connect_todo = df_connect


fs = args.fs
lst = args.lst
dt = args.dt
tck = args.tck
tvb = args.tvb

###############
outputs = Parallel(n_jobs=args.njobs, backend="threading")(
    delayed(run_pipeline)(
        row, df_pip_status, out_dir, subj_list, base_data_dir, fs, lst, dt, tck, tvb
    )
    for row in df_connect_todo.itertuples()
)
