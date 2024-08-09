#!/bin/bash
#SBATCH --time=00-02:00:00 # days-hh:mm:ss
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=1 
#SBATCH --mem=3G

source ~/.bashrc  # need to set up the normal environment.

source /cluster/tufts/mggg/cdonna01/.venv_stv_prop/bin/activate
# cd into the correct directory
cd /cluster/tufts/mggg/cdonna01/EC_paper/scottish/draft_2

election=$1
model=$2
bloc_order=$3
log_file=$4

python 1_bloc_optimize.py "$election" \
            "$model" \
            "$bloc_order" 
sacct -j $SLURM_JOB_ID --format=JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,NCPUS,NNodes,NodeList,ReqMem,MaxRSS,AllocCPUS,Timelimit,TotalCPU >> "$log_file" 2>> "$log_file"