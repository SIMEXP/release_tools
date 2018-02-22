% Options for the sge qsub system, example : '-q all.q'
% will result in 
% > qsub -q all.q
% to be used when submiting PSOM workers  
%gb_psom_qsub_options = '-q all.q';
gb_psom_qsub_options = '';

% Options for the execution mode of the pipeline 
% use "session" to do a test with one (1) worker run on the local node
% use "background" to do a run on the local with gb_psom_max_queued workers
% use "singularity" for full fledge PSOM usage on the HPC
gb_psom_mode = 'session';
%gb_psom_mode = 'background';
%gb_psom_mode = 'singularity';

% Options for the maximal number of jobs
% 
gb_psom_max_queued = 12;


