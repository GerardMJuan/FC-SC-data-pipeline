# FC-SC-data-pipeline

Pipeline for TVB processing for the journal articles:

- Gerard Martí-Juan, Jaume Sastre-Garriga, Eloy Martinez-Heras, Angela Vidal-Jordana, Sara Llufriu, Sergiu Groppa, Gabriel Gonzalez-Escamilla, Maria A Rocca, Massimo Filippi, Einar A Høgestøl, Hanne F Harbo, Michael A Foster, Ahmed T Toosy, Menno M Schoonheim, Prejaas Tewarie, Giuseppe Pontillo, Maria Petracca, Àlex Rovira, Gustavo Deco, Deborah Pareto, **Using The Virtual Brain to study the relationship between structural and functional connectivity in patients with multiple sclerosis: a multicenter study**, Cerebral Cortex, 2023;, bhad041, https://doi.org/10.1093/cercor/bhad041

- And Gerard Martí-Juan et al. **Conservation of hemispheric brain connectivity in patients with Multiple Sclerosis**, In preparation.

## WARNING

Code is shared "as is", should not be considered as an automatic pipeline, foolproof or failproof. Some things could break. Run with caution.

## Quick description

This code applies a full pipeline to generate SC and FC matrices ready for TVB simulation. Each subject must have:

- T1 scan for segmentation.
- FLAIR for lesion segmentation.
- DTI for tracking.
- rsfMRI for FC generation.

The scripts are adapted for each of the centers used in the original work. For a new site, some parameters and options will probably need to be adapted too.

In all the scripts, for using, it is necessary to add the paths of the installed packages and libraries at the start of each one.

## Programs and main packages used

In no particular order.

- Python3
- MATLAB
- Mrtrix3 (https://www.mrtrix.org/)
- CONN (https://web.conn-toolbox.org/)
- LST (https://www.applied-statistics.de/lst.html)
- FastSurfer (https://github.com/Deep-MI/FastSurfer)
- FSL (https://fsl.fmrib.ox.ac.uk/fsl/fslwiki)

## Files description

- run_pipeline_prime.py: Runs the whole pipeline. See the file for options. Different parts of the pipeline can be selected, and also can be run in parallel.
- run_CONN.py: Separate pipeline that processes the fMRI using CONN to obtain the FC in the TVB format.
- average_matrices.py: Average all the matrices of the healthy controls already generated of a single center.
- check_all_pips.py: Check the state of preprocessing for each subject and preprocesing step.
- check_qc.py: Generates quality control images for the processed subjects.
- create_unified_csv.py: Combines . Not directly relevant, although the output format of the csv is the one used by the pipeline.
- move_completed_subjects.py: Moves completed preprocessed subjects to a different directory.

## Credits

- Michael Schirner, Simon Rothmeier, Petra Ritter for parts of the code adapted from their TVB pipeline (those are cited specifically for each script) https://github.com/BrainModes/TVB-empirical-data-pipeline An automated pipeline for constructing personalized virtual brains from multimodal neuroimaging data. NeuroImage.
- Eloy Martínez de las Heras for their help for the diffusion processing and their approach to remove implausible streamlines, described in more detail in https://doi.org/10.1371/journal.pone.0137064.
- Gerard Martí-Juan (gerardmartijuan(at)(ge)mail.com)

## License

MIT License. See LICENSE file for details.
