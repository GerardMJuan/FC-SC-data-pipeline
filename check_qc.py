"""
Set of functions to clean up the non-essential files of each step 
of the preprocessing pipeline.

Each step needs to have an own function to properly work

Also, generate comparison images and values that are useful to rapidly assess
the correctness of the preprocessing steps.

Use this class:
https://raamana.github.io/mrivis/readme.html

Compute SSIM between intermediate images
"""

import numpy as np
import os
import mrivis
from mrivis.utils import read_image, scale_0to1
import matplotlib.pyplot as plt
import click
import subprocess
import numpy as np
import glob
import pandas as pd


def run_checks(subj_dir, type_dir, out_dir, fs, lst, dt, fc, track, matrix_plot):
    """
    General function to run the checks.
    Flag inputs will select the evaluation functions to run.
    """

    # check if subject exists
    if not os.path.exists(subj_dir):
        raise NotADirectoryError(f"{subj_dir} is not a valid directory!")

    # create output dir
    # all files should be in the same folder for easy viewing, with a prefix indicating to which
    # step they refer

    subID = os.path.basename(subj_dir.rstrip("/"))
    print(f"Running QC for... {subID}")

    if not os.path.exists(f"{out_dir}/{type_dir}_{subID}"):
        os.makedirs(f"{out_dir}/{type_dir}_{subID}")

    out_dir = f"{out_dir}/{type_dir}_{subID}"

    # Run specific tests
    # Each function should return an exception if the files that we are
    # if QC has already run, dont do it again
    """
    if fs and not os.path.isfile(f'{out_dir}/1fs_seg_overlay2.png'):
        try:
            check_FastSurfer(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print('Freesurfer QC failed!')
    """
    """
    if lst and not os.path.isfile(f'{out_dir}/{subID}_2flair_lesionseg_dil.png'):
        try:
            check_LesionSeg(subj_dir, out_dir, subID)
        except (FileNotFoundError, IOError) as e:
            print('LesionSegmentation QC failed!')
    
    if dt and not os.path.isfile(f'{out_dir}/{subID}_2dt_t1_seg_overlay.png'):
        try:
            check_DTrecon(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print("DT_recon QC failed!")
    """
    """
    if dt and not os.path.isfile(f'{out_dir}/{subID}_3dtmask_checkbiascorrect.png'):
        try:
            check_DTMask(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print("DT_recon Mask QC failed!")
    """
    """
    if fc and not os.path.isfile(f'{out_dir}/{subID}_6fmri_t1_checkerboard.png'): 
        try:
            check_fMRI(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print('fMRI QC failed!')
    
    if track and not os.path.isfile(f'{out_dir}/{subID}_track_tdi_count_AEC.png'): 
        try:
            check_Tracking(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print('Tracking QC failed!')
    """
    if matrix_plot and not os.path.isfile(f"{out_dir}/{subID}_9fig_FChist.png"):
        try:
            plot_connectivity(subj_dir, out_dir, subID)
        except FileNotFoundError:
            print("Connectivity FC failed!")


def check_FastSurfer(subj_dir, out_dir, subID):
    """
    What to check:
    - Visually check the segmentation over the T1
    - Visually check the brain extraction
    - Get some key values of volumes and cort thickness

    Input:
        subj_dir: directory containing all the processed folders.
        out_dir: out directory where the pictures and values will reside

    The scripts also checks that the necessary files generated by FS exist, and if not, raises
    an exception
    """
    # We assume that recon_all is in the root of subj_dir
    recon_all_path = f"{subj_dir}/recon_all"
    # T1 and brain should be already in nii if FastSurfer.sh has been run
    # check that they exist
    t1_path = f"{recon_all_path}/mri/T1.nii.gz"
    brain_path = f"{recon_all_path}/mri/norm.nii.gz"
    seg_path = f"{recon_all_path}/mri/aparc.DKTatlas+aseg.nii.gz"

    if not (
        os.path.exists(t1_path)
        and os.path.exists(brain_path)
        and os.path.exists(seg_path)
    ):
        raise FileNotFoundError(
            "Files generated by FS not found. Make sure that the pipeline has run correctly!"
        )

    # load and scale images
    t1 = scale_0to1(read_image(t1_path, None))
    brain = scale_0to1(read_image(brain_path, None))
    seg = scale_0to1(read_image(seg_path, None))

    ## COLLAGE OF T1
    collage = mrivis.Collage()
    collage.attach(t1)
    collage.save(output_path=f"{out_dir}/{subID}_fs_t1_collage")
    plt.close()

    ## COLLAGE OF BRAIN
    collage = mrivis.Collage()
    collage.attach(brain)
    collage.save(output_path=f"{out_dir}/{subID}_fs_brain_collage")
    plt.close()

    ## OVERLAY BETWEEN SEGMENTATION AND BRAIN
    mrivis.color_mix(
        brain,
        seg,
        num_slices=10,
        alpha_channels=(1, 1),
        output_path=f"{out_dir}/{subID}_1fs_seg_overlay2",
    )
    plt.close()


def check_LesionSeg(subj_dir, out_dir, subID):
    """
    Check the lesion segmentation done by the LST toolbox.
    - Visualize the lesions
    - Visualize the dilated lesions
    - Over the T1
    - Check registration between T1 and FLAIR
    """

    # We assume that recon_all is in the root of subj_dir
    recon_all_path = f"{subj_dir}/recon_all"
    dt_proc_path = f"{subj_dir}/dt_proc"

    # paths
    try:
        seg_path = glob.glob(f"{dt_proc_path}/r*_ROI_00_256.nii.gz")[0]
        seg_dil_path = f"{dt_proc_path}/lesions_dilated_std.nii.gz"
    except:
        print("Segmentation not found!")
        return 0
    t1_path = f"{recon_all_path}/mri/T1.nii.gz"
    flair_path = None
    if len(glob.glob(f"{subj_dir}/lst/FLAIR2T1.nii.gz")) > 0:
        flair_path = f"{subj_dir}/lst/FLAIR2T1.nii.gz"
    elif len(glob.glob(f"{subj_dir}/anat/FLAIR2T1.nii.gz")) > 0:
        flair_path = f"{subj_dir}/anat/FLAIR2T1.nii.gz"

    t1 = scale_0to1(read_image(t1_path, None))
    seg_dil = scale_0to1(read_image(seg_dil_path, None))
    seg = scale_0to1(read_image(seg_path, None))

    if flair_path is not None:
        os.system(f"mri_convert -c -rt nearest {flair_path} {flair_path}_256.nii.gz")
        flair = scale_0to1(read_image(f"{flair_path}_256.nii.gz", None))

    # show the lesions over the T1
    ## OVERLAY BETWEEN SEGMENTATION AND BRAIN
    if flair_path is not None:
        # mrivis.color_mix(flair, seg, num_slices=10, alpha_channels=(1, 0.2), output_path=f'{out_dir}/2flair_lesionseg')
        # plt.close()
        mrivis.color_mix(
            flair,
            seg_dil,
            num_slices=10,
            alpha_channels=(1, 0.3),
            output_path=f"{out_dir}/{subID}_2flair_lesionseg_dil",
        )
        plt.close()
    else:
        # if flair not available
        # mrivis.color_mix(t1, seg, num_slices=10, alpha_channels=(1, 0.2), output_path=f'{out_dir}/2flair_lesionseg')
        # plt.close()
        mrivis.color_mix(
            t1,
            seg_dil,
            num_slices=10,
            alpha_channels=(1, 0.3),
            output_path=f"{out_dir}/{subID}_2flair_lesionseg_dil",
        )
        plt.close()

    if flair_path is not None:
        mrivis.checkerboard(
            flair, t1, patch_size=15, output_path=f"{out_dir}/{subID}_2flair_t1_check"
        )
        plt.close()


def check_DTMask(subj_dir, out_dir, subID):
    """
    Check the mask generated from the dwi, to see if the dwbiascorrect
    has affected positively or negatively
    """
    dwi = f"{subj_dir}/dt_proc/mean_b0_preprocessed.nii.gz"
    dwi_mask = f"{subj_dir}/dt_proc/dwi_ec_unbiased_mask.nii.gz"

    # check paths existing

    # load the images
    dwi = scale_0to1(read_image(dwi, None))
    dwi_mask = scale_0to1(read_image(dwi_mask, None))

    mrivis.color_mix(
        dwi_mask,
        dwi,
        num_slices=10,
        alpha_channels=(0.3, 1.0),
        output_path=f"{out_dir}/{subID}_3dtmask_checkbiascorrect",
    )
    plt.close()


def check_DTrecon(subj_dir, out_dir, subID):
    """
    What to check:
    - Visualize processing of DT, Comparing d0 at unproc and proc
    - Visualize processing of DT, visualizing carpet
    - Visualize registration between DT and T1
    - VIsualization of FA image, FA matrix
    - Visualize 5TT over DT (5tt2vis)

    Input:
        subj_dir: directory containing all the processed folders.

    We assume that the DT_recon step of the pipeline has been run beforehand.
    """

    # paths of relevant images
    og_b0 = f"{subj_dir}/dt_proc/dwi_b0.nii.gz"
    proc_b0 = f"{subj_dir}/dt_proc/mean_b0_preprocessed.nii.gz"
    FA = f"{subj_dir}/dt_recon/fa.nii.gz"
    seg5tt = f"{subj_dir}/dt_proc/5tt2diff_3d.nii.gz"
    t1 = f"{subj_dir}/recon_all/mri/norm.nii.gz"
    seg5tt_wm = f"{subj_dir}/dt_proc/5tt.wm.nii.gz"
    seg5tt_csf = f"{subj_dir}/dt_proc/5tt.csf.nii.gz"

    # check paths existing
    if not (
        os.path.exists(og_b0)
        and os.path.exists(proc_b0)
        and os.path.exists(FA)
        and os.path.exists(seg5tt)
        and os.path.exists(seg5tt_wm)
        and os.path.exists(seg5tt_csf)
        and os.path.exists(t1)
    ):
        raise FileNotFoundError(
            "Files generated by DTRecon not found. Make sure that the pipeline has run correctly!"
        )

    # do I need to load the images, similar to the previous one? sure
    og_b0 = scale_0to1(read_image(og_b0, None))
    proc_b0 = scale_0to1(read_image(proc_b0, None))
    FA = scale_0to1(read_image(FA, None))
    seg5tt = scale_0to1(read_image(seg5tt, None))
    t1 = scale_0to1(read_image(t1, None))
    seg5tt_wm = scale_0to1(read_image(seg5tt_wm, None))
    seg5tt_csf = scale_0to1(read_image(seg5tt_csf, None))

    # collage of DT b0, not processed
    collage = mrivis.Collage()
    collage.attach(og_b0)
    collage.save(output_path=f"{out_dir}/{subID}_dt_b0_unproc")
    plt.close()

    # collage of DT b0, processed
    collage = mrivis.Collage()
    collage.attach(proc_b0)
    collage.save(output_path=f"{out_dir}/{subID}_dt_b0_proc")
    plt.close()

    # FA image, visualization
    collage = mrivis.Collage()
    collage.attach(FA)
    collage.save(output_path=f"{out_dir}/{subID}_dt_FA")
    plt.close()
    # visualize 5tt.wm and 5tt.csf (will be useful also for later)
    # collage = mrivis.Collage()
    # collage.attach(seg5tt_wm)
    # collage.save(output_path=f'{out_dir}/dt_5ttwm')
    # plt.close()

    # registration between T1 and wm (color mix)
    # TODO DO COLOR MIX
    mrivis.color_mix(
        t1,
        seg5tt_wm,
        num_slices=10,
        alpha_channels=(1, 1),
        output_path=f"{out_dir}/{subID}_dt_reg_t1_wm",
    )
    # mrivis.checkerboard(t1, seg5tt_wm)
    # plt.savefig(f'{out_dir}/dt_reg_t1_wm.png')
    plt.close()

    # collage = mrivis.Collage()
    # collage.attach(seg5tt_csf)
    # collage.save(output_path=f'{out_dir}/dt_5ttcsf')
    # plt.close()

    # registration between T1 and wm (color mix)
    # TODO DO COLOR MIX
    mrivis.color_mix(
        t1,
        seg5tt_csf,
        num_slices=10,
        alpha_channels=(1, 1),
        output_path=f"{out_dir}/{subID}_dt_reg_t1_csf",
    )
    # mrivis.checkerboard(t1, seg5tt_csf)
    # plt.savefig(f'{out_dir}/dt_reg_t1_csf.png')
    plt.close()

    # 5TT over T1 (color mix)
    # mrivis.color_mix(t1, seg5tt, num_slices=10, alpha_channels=(1,1), output_path=f'{out_dir}/dt_seg_overlay')
    # plt.close()

    # 5TT over DT (color mix)
    mrivis.color_mix(
        proc_b0,
        seg5tt,
        num_slices=10,
        alpha_channels=(1, 0.7),
        output_path=f"{out_dir}/{subID}_2dt_t1_seg_overlay",
    )
    plt.close()


def check_Tracking(subj_dir, out_dir, subID):
    """
    What to check:
    - visualize tracking (over DTI)
    - https://mrtrix.readthedocs.io/en/latest/reference/commands/tckmap.html#tckmap
    - https://mrtrix.readthedocs.io/en/latest/reference/commands/mrview.html#mrview

    This could probably have to be extended

    IN TRACKING, I DO A
    """

    # check that files exists
    dwi_proc = f"{subj_dir}/dt_proc/mean_b0_preprocessed.nii.gz"
    tracks_AEC = f"{subj_dir}/dt_proc/brain_track_AEC.tck"
    sift_weights = f"{subj_dir}/dt_proc/brain_track.txt"

    # check paths existing
    if not (
        os.path.exists(dwi_proc)
        and os.path.exists(tracks_AEC)
        and os.path.exists(sift_weights)
    ):
        raise FileNotFoundError(
            "Files generated by DTRecon not found. Make sure that the pipeline has run correctly!"
        )

    output_file = f"{out_dir}/log_qctrack.txt"
    # redirect all output to file
    with open(output_file, "w") as f:
        cmd = subprocess.Popen(
            f"exec scripts/QC_track.sh {subj_dir} {out_dir} {subID}",
            shell=True,
            stdout=f,
            stderr=f,
        )
        cmd.wait()

    # check if the script has worked (this is, )
    # tdi_count_AEC = f'{out_dir}/track_tdi_count_AEC.nii.gz'
    # tdi_fractional_AEC = f'{out_dir}/track_tdi_fractional_AEC.nii.gz'
    anat2diff = f"{subj_dir}/dt_proc/anat2diff.nii.gz"
    nodes2diff = f"{subj_dir}/dt_proc/nodes2diff.nii.gz"

    # load images for collage
    dwi_proc = scale_0to1(read_image(dwi_proc, None))
    # tdi_count_AEC = scale_0to1(read_image(tdi_count_AEC, None))
    # tdi_fractional_AEC = scale_0to1(read_image(tdi_fractional_AEC, None))
    anat2diff = scale_0to1(read_image(anat2diff, None))
    nodes2diff = scale_0to1(read_image(nodes2diff, None))

    # check registration of anat and dti
    mrivis.checkerboard(
        dwi_proc,
        anat2diff,
        patch_size=15,
        output_path=f"{out_dir}/{subID}_3track_anat2diff_checkerboard",
    )
    plt.close()

    mrivis.color_mix(
        anat2diff,
        dwi_proc,
        num_slices=10,
        alpha_channels=(1, 0.7),
        output_path=f"{out_dir}/{subID}_4track_t1_seg_overlay",
    )
    plt.close()

    mrivis.color_mix(
        dwi_proc,
        nodes2diff,
        num_slices=10,
        alpha_channels=(1, 0.7),
        output_path=f"{out_dir}/{subID}_track_nodes2diff_overlay",
    )
    # mrivis.checkerboard(dwi_proc, nodes2diff, patch_size=15, output_path=f'{out_dir}/track_nodes2diff_overlay')
    plt.close()

    # create collage of that prob mask
    # collage of DT b0, processed
    # collage = mrivis.Collage()
    # collage.attach(tdi_count_AEC)
    # collage.save(output_path=f'{out_dir}/{subID}_track_tdi_count_AEC')
    # plt.close()


def check_fMRI(subj_dir, out_dir, subID):
    """
    Check the intermediate steps of the fMRI pipeline (mask, regression, correlation across specific points)
    to have a clear idea that everything has gone well
    """

    fmri_mean_brain = f"{subj_dir}/fmri_proc_dti/mean_func_brain.nii.gz"
    # fmri2t1 = f'{subj_dir}/fmri_proc/func2t1.nii.gz'
    t1 = f"{subj_dir}/recon_all/mri/norm.nii.gz"

    if not (os.path.exists(fmri_mean_brain) and os.path.exists(t1)):
        raise FileNotFoundError(
            "Files generated by fMRIPROC not found. Make sure that the pipeline has run correctly!"
        )

    fmri_mean_brain = scale_0to1(read_image(fmri_mean_brain, None))
    t1 = scale_0to1(read_image(t1, None))
    # fmri2t1 = scale_0to1(read_image(fmri2t1, None))

    # mean func brain
    collage = mrivis.Collage()
    collage.attach(fmri_mean_brain)
    collage.save(output_path=f"{out_dir}/{subID}_fmri_mean_brain")
    plt.close()

    # check alignment with T1
    # mrivis.color_mix(fmri2t1, t1, num_slices=10, alpha_channels=(0.7,0.7), output_path=f'{out_dir}/5fmri_t1_overlay')
    # plt.close()
    # mrivis.checkerboard(fmri2t1, t1, patch_size=15, output_path=f'{out_dir}/6fmri_t1_checkerboard')
    # plt.close()


def plot_connectivity(subj_dir, out_dir, subID):
    """
    For a subject, create a figure for the structural and functional connectivity matrices

    Input:
        subj_dir: directory containing all the processed folders.
        out_folder: name of the folder to put the images (will go inside subj_dir, and will be created if doesnt exist)

    """
    # load matrices from disk
    # TODO: LOAD THE NORMALIZED SC WEIGHTS WHEN IMPLEMENTED?
    SC_path_weight = f"{subj_dir}/dt_proc/connectome_weights.csv"
    SC_path_length = f"{subj_dir}/dt_proc/connectome_lengths.csv"

    r_mat = f"{subj_dir}/fmri_proc_dti/r_matrix.csv"
    zr_mat = f"{subj_dir}/fmri_proc_dti/zr_matrix.csv"
    corrlabel_ts = f"{subj_dir}/fmri_proc_dti/corrlabel_ts.txt"

    if not (os.path.exists(SC_path_weight) and os.path.exists(SC_path_length)):
        raise FileNotFoundError(
            "SC matrices not found. Make sure that the pipeline has been run correctly!"
        )

    """
    if not (os.path.exists(r_mat) and os.path.exists(zr_mat) and os.path.exists(corrlabel_ts)):
        raise FileNotFoundError("FC matrices not found. Make sure that the pipeline has been run correctly!")
    """
    SC_weight = np.loadtxt(SC_path_weight, delimiter=",")
    SC_length = np.loadtxt(SC_path_length, delimiter=",")

    r_mat = np.loadtxt(r_mat, delimiter=",")
    zr_mat = np.loadtxt(zr_mat, delimiter=",")

    plt.figure(figsize=(10, 4))
    plt.subplot(121), plt.title("weights"), plt.imshow(
        SC_weight, interpolation="none"
    ), plt.colorbar()
    plt.subplot(122), plt.title("lengths"), plt.imshow(
        SC_length, interpolation="none"
    ), plt.colorbar()
    plt.savefig(f"{out_dir}/{subID}_7fig_SC.png")
    plt.close()

    # load matrices from disk
    plt.figure(figsize=(15, 4))
    plt.subplot(121), plt.title("Corr"), plt.imshow(
        r_mat, interpolation="none"
    ), plt.colorbar()
    plt.subplot(122), plt.title("Norm Corr"), plt.imshow(
        zr_mat, interpolation="none"
    ), plt.colorbar()
    plt.savefig(f"{out_dir}/{subID}_8fig_FC.png")
    plt.close()
    """
    # compute histogram of FC and norm FC
    plt.figure(figsize=(15, 4))
    plt.subplot(121), plt.title('Hist. Corr'), plt.hist(r_mat)
    plt.subplot(122), plt.title('Hist. Norm Corr'), plt.hist(zr_mat)
    plt.savefig(f'{out_dir}/9fig_FChist.png')
    plt.close()
    """
    """
    # compute bold from specific regions (regions collindant with each other, f. ex.) as a sanity check
    corr_ts = np.loadtxt(corrlabel_ts)

    # indexs to use
    idx = [(5, 12), (27, 58), (16, 47)]
    names = [("L_Hippocampus", "R_Hippocampus"), ("L_MiddleTemporal", "R_MiddleTemporal"), ("L_CaudalMiddleFrontal", "R_CaudalMiddleFrontal")]

    for ((id1, id2), (name1, name2)) in zip(idx, names):
        # create plot
        plt.figure(figsize=(12, 3))
        # need to demean!
        plt.plot(range(len(corr_ts[:, id1-1])), corr_ts[:,id1-1] - np.mean(corr_ts[:,id1-1]), c='r', label=name1)
        plt.plot(range(len(corr_ts[:, id2-1])), corr_ts[:,id2-1] - np.mean(corr_ts[:,id2-1]), c='b', label=name2)
        plt.legend()
        plt.savefig(f'{out_dir}/fig_FC_{name1}.png')
        plt.close()
    """


# example: python check_qc.py --out_dir /home/extop/GERARD/DATA/MAGNIMS2021/qc --subj_list test_ams_london.txt --pip_csv /home/extop/GERARD/DATA/MAGNIMS2021/pipeline.csv /home/extop/GERARD/DATA/MAGNIMS2021
# flags could be defined by the pipeline.csv: if that column is True, we


@click.command(
    help="Perform a quality check of the preprocessing pipeline over all subjects. By default, ."
)
@click.option("--out_dir", default="qc")
@click.option(
    "--subj_list", type=click.STRING, help="Txt list with the subjects we want to qc"
)
@click.option(
    "--pip_csv",
    required=True,
    type=click.STRING,
    help="csv with the current pipeline information for every subject",
)
@click.argument("subj_dir")
def run_all_subjects(subj_dir, out_dir, subj_list, pip_csv):
    """
    Run over all subjects
    """

    df_pipeline = pd.read_csv(pip_csv)
    df_pipeline_todo = pd.DataFrame(columns=df_pipeline.columns, dtype=object)

    if subj_list is not None and os.path.exists(subj_list):
        subj_list = np.genfromtxt(subj_list, delimiter=",", dtype="str")
        for s in subj_list:
            # s[0] should be the id, s[1] should be the center
            # df_pipeline_todo = df_pipeline_todo.append(df_pipeline[(df_pipeline.id == s[0])]) # will select subjects taht we don't have to process
            df_pipeline_todo = df_pipeline_todo.append(
                df_pipeline[(df_pipeline.id == s[0]) & (df_pipeline.CENTER == s[1])]
            )  # will select subjects taht we don't have to process

    else:
        subj_list = []
        df_pipeline_todo = df_pipeline

    for row in df_pipeline_todo.itertuples():
        subID = row.id
        type_dir = row.CENTER

        subj_dir_id = f"{subj_dir}/{type_dir}_Post/{subID}"

        # run qc only in steps that have been done
        fs = row.fastsurfer
        lst = True  # we assume truth, and if it fails, it fails
        dt = row.DWI_preproc
        fc = row.fMRI
        track = row.agg_SC
        matrix_plot = True  # and fc

        # apply pipelines
        # try:
        run_checks(subj_dir_id, type_dir, out_dir, fs, lst, dt, fc, track, matrix_plot)
        # except:
        #     print(f"Something weird went on with {subID}")
        #     continue


if __name__ == "__main__":
    # those parameters have to be entered from outside
    run_all_subjects()
