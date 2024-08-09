#!/bin/bash
#SBATCH --time=00-00:05:00 # days-hh:mm:ss
#SBATCH --nodes=1 # how many computers do we need?
#SBATCH --ntasks-per-node=1 # how many cores per node do we need?
#SBATCH --mem=3G # how many MB of memory do we need (2GB here)

source ~/.bashrc  # need to set up the normal environment.

source /cluster/tufts/mggg/cdonna01/.venv_stv_prop/bin/activate
# cd into the correct directory
cd /cluster/tufts/mggg/cdonna01/EC_paper/refactored_2_bloc_stv

N_TRIALS=$1
N_BALLOTS=$2
N_SEATS=$3
N_CANDS_PER_BLOC=$4
fpv_b=$5
fpv_a=$6
b_prop=$7
g=$8
pi_type=$9
log_file=${10}

python fixed_intervals_2_bloc_stv.py "$N_TRIALS" \
            "$N_BALLOTS" \
            "$N_SEATS" \
            "$N_CANDS_PER_BLOC" \
            "$fpv_b" \
            "$fpv_a" \
            "$b_prop" \
            "$g" \
            "$pi_type" 
sacct -j $SLURM_JOB_ID --format=JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,NCPUS,NNodes,NodeList,ReqMem,MaxRSS,AllocCPUS,Timelimit,TotalCPU >> "$log_file" 2>> "$log_file"