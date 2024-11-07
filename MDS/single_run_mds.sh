#!/bin/bash
#SBATCH --time=00-02:00:00 # days-hh:mm:ss
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=1 
#SBATCH --mem=3G

source ~/.bashrc  # need to set up the normal environment.

source /cluster/tufts/mggg/cdonna01/.venv_stv_prop/bin/activate
# cd into the correct directory
cd /cluster/tufts/mggg/cdonna01/EC_paper/MDS

metric=$1
b_coh=$2
log_file=$3

python mds_plots.py "$metric" \
            "$b_coh" 
sacct -j $SLURM_JOB_ID --format=JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,NCPUS,NNodes,NodeList,ReqMem,MaxRSS,AllocCPUS,Timelimit,TotalCPU >> "$log_file" 2>> "$log_file"