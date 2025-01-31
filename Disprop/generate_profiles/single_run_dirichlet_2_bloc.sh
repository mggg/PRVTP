#!/bin/bash
#SBATCH --time=00-00:30:00 # days-hh:mm:ss
#SBATCH --nodes=1 # how many computers do we need?
#SBATCH --ntasks-per-node=1 # how many cores per node do we need?
#SBATCH --mem=3G # how many MB of memory do we need (2GB here)

source ~/.bashrc  # need to set up the normal environment.
# cd into the correct directory
cd /cluster/tufts/mggg/cdonna01/PRVTP_feb_25_submission/generate_profiles
source ../.venv_prvtp/bin/activate

N_TRIALS=$1
N_BALLOTS=$2
N_SEATS=$3
N_CANDS_PER_BLOC=$4
sd=$5
ud=$6
fpv_b=$7
fpv_a=$8
b_prop=$9
g=${10}
pi_type=${11}
log_file=${12}

python dirichlet_2_bloc_profiles.py $N_TRIALS \
            $N_BALLOTS \
            $N_SEATS \
            $N_CANDS_PER_BLOC \
            $sd \
            $ud \
            $fpv_b \
            $fpv_a \
            $b_prop \
            $g \
            $pi_type 
sacct -j $SLURM_JOB_ID --format=JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,NCPUS,NNodes,NodeList,ReqMem,MaxRSS,AllocCPUS,Timelimit,TotalCPU >> "$log_file" 2>> "$log_file"