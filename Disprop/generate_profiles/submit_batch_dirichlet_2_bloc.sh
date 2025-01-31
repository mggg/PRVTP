#!/bin/bash

# This script is meant to act as a sentinel to submit
# jobs to the slurm scheduler. The main idea is that the
# running script will be the one that calls the process
# that takes up the most time 



# ==============
# JOB PARAMETERS
# ==============

# This is the identifier that slurm will use to help
# keep track of the jobs. Please make sure that this
# does not exceed 80 characters.
job_name="dirichlet_2_bloc_stv_$(date '+%d-%m-%Y@%H:%M:%SET')"
sleep_length=30
# This controls how many jobs the scheduler will
# see submitted at the same time.
max_concurrent_jobs=250

# This is the name of the script that will be run
# to actually process all of the files and do the 
# you may need to modify the call to this script
# on line 167 or so
running_script_name="single_run_dirichlet_2_bloc.sh"

##### this took 7hrs 8.5 min to run!
# ==================
# RUNNING PARAMETERS
# ==================
log_dir="logs/dirichlet"
N_TRIALS=100
N_BALLOTS=5000
N_SEATS=5
N_CANDS_PER_BLOC=5
u_dirichlets=(2) #(2 10 100)
#s_dirichlets=(.5) #(.5 .1 .01) # conditioned on u later 
fpv_bs=(.55 .65 .75 .85 .95)
fpv_as=(.55 .65 .75 .85 .95)
b_props=(.05 .15 .25 .35 .45 .55 .65 .75 .85 .95)
generators=("slate-BT" "slate-CS-W" "slate-CS-C" "slate-PL")
pi_types=("UU" "UX" "XXsame" "XXdif") 
 


# ===============================================================
# Ideally, you should not need to modify anything below this line
# However, you may need to modify the call on line 167
# ===============================================================

mkdir -p "${log_dir}"

job_ids=()
job_index=0

echo "========================================================"
echo "The job name is: $job_name"
echo "========================================================"

# This function will generate a label for the log and output file
generate_file_label() {
    local N_TRIALS="$1"
    local N_BALLOTS="$2"
    local N_SEATS="$3"
    local N_CANDS_PER_BLOC="$4"
    local sd="$5"
    local ud="$6"
    local fpv_b="$7"
    local fpv_a="$8"
    local b_prop="$9"
    local g="${10}"
    local pi_type="${11}"


    # Use string substistution to replace spaces with dashes
    # This will make the files nicer to work with in the command line
    echo "n_trials_${N_TRIALS// /-}"\
        "n_ballots_${N_BALLOTS// /-}"\
        "n_seats_${N_SEATS// /-}"\
        "ncands_${N_CANDS_PER_BLOC// /-}"\
        "sd_${sd// /-}"\
        "ud_${ud// /-}"\
        "fpv_b_${fpv_b// /-}"\
        "fpv_a_${fpv_a// /-}"\
        "b_prop_${b_prop// /-}"\
        "g_${g// /-}"\
        "pi_type_${pi_type// /-}"\
        | tr ' ' '_'
    # The tr command replaces spaces with underscores so that
    # the file names are a bit nicer to read
}


# Indentation modified for readability
# for sd in "${s_dirichlets[@]}"; do
for ud in "${u_dirichlets[@]}"; do
    if [ $ud ==  2 ]; then
        sd=.5
    elif [ $ud == 10 ]; then
        sd=.1
    else
        sd=.01
    fi
for fpv_b in "${fpv_bs[@]}"; do
for fpv_a in "${fpv_as[@]}"; do
for b_prop in "${b_props[@]}"; do
for g in "${generators[@]}"; do
for pi_type in "${pi_types[@]}"; do

    file_label=$(generate_file_label \
        "$N_TRIALS" \
        "$N_BALLOTS" \
        "$N_SEATS" \
        "$N_CANDS_PER_BLOC" \
        "$sd" \
        "$ud" \
        "$fpv_b" \
        "$fpv_a" \
        "$b_prop" \
        "$g" \
        "$pi_type" \
    )
    
    log_file="${log_dir}/${file_label}.log"

    # Waits for the current number of running jobs to be
    # less than the maximum number of concurrent jobs
    while [[ ${#job_ids[@]} -ge $max_concurrent_jobs ]] ; do
        # Check once per minute if there are any open slots
        sleep $sleep_length
        # We check for the job name, and make sure that squeue prints
        # the full job name up to 100 characters
        job_count=$(squeue --name=$job_name --Format=name:100 | grep $job_name | wc -l)
        if [[ $job_count -lt $max_concurrent_jobs ]]; then
            break
        fi
    done

    # Some logging for the 
    for job_id in "${job_ids[@]}"; do
        if squeue -j $job_id 2>/dev/null | grep -q $job_id; then
            continue
        else
            job_ids=(${job_ids[@]/$job_id})
            echo "Job $job_id has finished or exited."
        fi
    done

    # This output will be of the form "Submitted batch job 123456"
    job_output=$(sbatch --job-name=${job_name} \
        --output="${log_file}" \
        --error="${log_file}" \
        $running_script_name \
            "$N_TRIALS" \
            "$N_BALLOTS" \
            "$N_SEATS" \
            "$N_CANDS_PER_BLOC" \
            "$sd" \
            "$ud" \
            "$fpv_b" \
            "$fpv_a" \
            "$b_prop" \
            "$g" \
            "$pi_type" \
            "$log_file"
    )
    
    # Extract the job id from the output. The awk command
    # will print the last column of the output which is
    # the job id in our case
    # 
    # Submitted batch job 123456
    #                     ^^^^^^
    job_id=$(echo "$job_output" | awk '{print $NF}')
    echo "Job output: $job_output"
    # Now we add the job id to the list of running jobs
    job_ids+=($job_id)
    # Increment the job index. Bash allows for sparse
    # arrays, so we don't need to worry about any modular arithmetic
    # nonsense
    job_index=$((job_index + 1))
done
done
done
done
done
done


# This is just a helpful logging line to let us know that all jobs have been submitted
# and to tell us what is still left to be done
printf "No more jobs need to be submitted. The queue is\n%s\n" "$(squeue --name=$job_name)"
# Check once per minute until the job queue is empty
while [[ ${#job_ids[@]} -gt 0 ]]; do
    sleep $sleep_length
    for job_id in "${job_ids[@]}"; do
        if squeue -j $job_id 2>/dev/null | grep -q $job_id; then
            continue
        else
            job_ids=(${job_ids[@]/$job_id})
            echo "Job $job_id has finished or exited."
        fi
    done

    job_ids=("${job_ids[@]}")
done

echo "All jobs have finished."