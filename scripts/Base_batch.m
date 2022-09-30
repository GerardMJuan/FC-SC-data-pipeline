function Base_batch(FUNCTIONAL_FILE, fs_dir, base_dir, TR, sliceorder, scans_to_remove)
%%% COPY TO THE CONN BASE DIRECTORY TO WORK
% This base example has as input the fmri scan, the t1 scan, and the TR.
% Loads the preprocessing done in the script, denoise, and analyze the RRC,
% saving everything to disk
% sliceorder also probably needs to be passed
% scans to remove, also

%% batch preprocessing for single-subject single-session data 

%% CONN New experiment
% assume it doesnt exist
batch.filename=fullfile(base_dir,'conn_FC.mat');

%% CONN Setup
batch.Setup.nsubjects=1;
batch.Setup.functionals{1}{1}=FUNCTIONAL_FILE;
batch.Setup.structurals{1}=fullfile(fs_dir, 'recon_all', 'mri', 'T1.mgz');
batch.Setup.RT=TR;
batch.Setup.conditions.names={'rest'};       
batch.Setup.conditions.onsets{1}{1}{1}=0;
batch.Setup.conditions.durations{1}{1}{1}=inf; 
batch.Setup.isnew=1;

batch.Setup.done=0;

% do this to import the aseg things
conn_batch(batch);
conn_importaseg;

batch.Setup.done=1;
batch.Setup.overwrite='Yes';

%% Load freesurfer ROI and WM, csf, GM
batch.Setup.rois.names = {'Grey Matter', 'White Matter', 'CSF', 'fs'};
batch.Setup.rois.files = {fullfile(fs_dir, 'recon_all', 'mri', 'c1_aseg.img') ...
                          fullfile(fs_dir, 'recon_all', 'mri', 'c2_aseg.img') ...
                          fullfile(fs_dir, 'recon_all', 'mri', 'c3_aseg.img') ...
                          fullfile(fs_dir, 'recon_all', 'mri', 'aparc.DKTatlas+aseg_newSeg.nii.gz')};

batch.Setup.rois.multiplelabels = [0,0,0,1];
batch.Setup.rois.regresscovariates = [0,1,1,0];
batch.Setup.rois.unsmoothedvolumes = [1,1,1,1];

%% Preprocessing steps
% remove slicetime for the ones that we dont have it 
%
batch.Setup.preprocessing.steps={'functional_label_as_original', 'functional_removescans', 'functional_realign&unwarp',... % 'functional_slicetime'... 
                                 'functional_art', 'functional_coregister_affine_reslice', 'functional_label_as_subjectspace', 'functional_smooth'...
                             	 'functional_label_as_smoothed'};
batch.Setup.preprocessing.sliceorder=sliceorder;
batch.Setup.preprocessing.removescans=scans_to_remove;

%% CONN Denoising
batch.Denoising.filter=[0.001, 0.08];          % frequency filter (band-pass values, in Hz)
batch.Denoising.done=1;
batch.Denoising.overwrite='Yes';
batch.Denoising.despiking=0;
batch.Denoising.detrending=1;
% Confound should be automatic

%% CONN Analysis
batch.Analysis.name='FC1';
batch.Analysis.type=1;
batch.Analysis.analysis_number=1;       % Sequential number identifying each set of independent first-level analyses
batch.Analysis.measure=1;               % connectivity measure used {1 = 'correlation (bivariate)', 2 = 'correlation (semipartial)', 3 = 'regression (bivariate)', 4 = 'regression (multivariate)';
batch.Analysis.weight=1;                % within-condition weight used {1 = 'none', 2 = 'hrf', 3 = 'hanning';
batch.Analysis.sources={};              % (defaults to all ROIs)
batch.Analysis.done=1;
batch.Analysis.overwrite=1;

%% QA
batch.QA.plots = {'QA_REG functional','QA_REG structural','QA_REG functional','QA_DENOISE histogram','QA_DENOISE timeseries','QA_DENOISE FC-QC'};
batch.QA.rois=4;
batch.QA.sets=0;

%% RUN
conn_batch(batch);

end