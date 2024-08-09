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
job_name="fixed_intervals_2_bloc_stv_$(date '+%d-%m-%Y@%H:%M:%SET')"
sleep_length=10
# This controls how many jobs the scheduler will
# see submitted at the same time.
max_concurrent_jobs=250

# This is the name of the script that will be run
# to actually process all of the files and do the 
# you may need to modify the call to this script
# on line 167 or so
running_script_name="single_run_fixed_intervals_2_bloc.sh"


# ==================
# RUNNING PARAMETERS
# ==================
log_dir="logs/fixed"
N_TRIALS=25
N_BALLOTS=1000
N_SEATS=6
N_CANDS_PER_BLOC=6
b_cohs=(.5 .55 .6 .65 .7 .75 .8 .85 .9 .95)
a_cohs=(.5 .55 .6 .65 .7 .75 .8 .85 .9 .95)
b_props=(.05 .1 .15 .2 .25 .3 .35 .4 .45 .5 .55 .6 .65 .7 .75 .8 .85 .9 .95)
generators="slate-BT" #("slate-BT" "slate-CS-W" "slate-CS-C" "slate-PL")
pi_types=("UU" "UX" "XX-same" "XX-dif")




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
    local b_coh="$5"
    local a_coh="$6"
    local b_prop="$7"
    local g="$8"
    local pi_type="$9"


    # Use string substistution to replace spaces with dashes
    # This will make the files nicer to work with in the command line
    echo "n_trials_${N_TRIALS// /-}"\
        "n_ballots_${N_BALLOTS// /-}"\
        "n_seats_${N_SEATS// /-}"\
        "ncands_${N_CANDS_PER_BLOC// /-}"\
        "b_coh_${b_coh// /-}"\
        "a_coh_${a_coh// /-}"\
        "b_prop_${b_prop// /-}"\
        "g_${g// /-}"\
        "pi_type_${pi_type// /-}"\
        | tr ' ' '_'
    # The tr command replaces spaces with underscores so that
    # the file names are a bit nicer to read
}

# Indentation modified for readability
for b_coh in "${b_cohs[@]}"; do
for a_coh in "${a_cohs[@]}"; do
for b_prop in "${b_props[@]}"; do
for g in "${generators[@]}"; do
for pi_type in "${pi_types[@]}"; do

    file_label=$(generate_file_label \
        "$N_TRIALS" \
        "$N_BALLOTS" \
        "$N_SEATS" \
        "$N_CANDS_PER_BLOC" \
        "$b_coh" \
        "$a_coh" \
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
            "$b_coh" \
            "$a_coh" \
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