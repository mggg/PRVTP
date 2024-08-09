#!/bin/bash
#SBATCH --time=00-00:10:00 # days-hh:mm:ss
#SBATCH --nodes=1 # how many computers do we need?
#SBATCH --ntasks-per-node=1 # how many cores per node do we need?
#SBATCH --mem=4G # how many MB of memory do we need (2GB here)

source ~/.bashrc  # need to set up the normal environment.

source /cluster/tufts/mggg/cdonna01/.venv_stv_prop/bin/activate
# cd into the correct directory
cd /cluster/tufts/mggg/cdonna01/EC_paper/refactored_2_bloc_stv

b_coh=$1
a_coh=$2
b_prop=$3
g=$4
pi_type=$5

echo "$b_coh" \
            "$a_coh" \
            "$b_prop" \
            "$g" \
            "$pi_type"

# python fixed_intervals_2_bloc_stv.py 25 1000 6 6 "$b_coh" \
#             "$a_coh" \
#             "$b_prop" \
#             "$g" \
#             "$pi_type"

python dirichlet_2_bloc_stv.py 100 1000 6 6 .5 2 "$b_coh" \
            "$a_coh" \
            "$b_prop" \
            "$g" \
            "$pi_type"