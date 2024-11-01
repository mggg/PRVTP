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
job_name="2_bloc_opt_$(date '+%d-%m-%Y@%H:%M:%SET')"
sleep_length=45
# This controls how many jobs the scheduler will
# see submitted at the same time.
max_concurrent_jobs=250

# This is the name of the script that will be run
# to actually process all of the files and do the 
# you may need to modify the call to this script
# on line 167 or so
running_script_name="single_run_2_bloc_opt.sh"


# ==================
# RUNNING PARAMETERS
# ==================
log_dir="logs/2_bloc"
elections=("fife 2022 21" "aberdeen 2017 12" "aberdeen 2022 12" "angus 2012 8" "falkirk 2017 6"\
              "clackmannanshire 2012 2" "renfrewshire 2017 1" "glasgow 2012 16" "north-ayrshire 2022 1")
models=("SB") #("CS-W" "CS-C" "SB" "s-PL" "s-BT" "IC" "IAC")
bloc_order="AB"




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
    local election="$1"
    local model="$2"
    local bloc_order="$3"


    # Use string substistution to replace spaces with dashes
    # This will make the files nicer to work with in the command line
    echo "election_${election// /-}"\
        "model_${model// /-}"\
        "bloc_order_${bloc_order// /-}"\
        | tr ' ' '_'
    # The tr command replaces spaces with underscores so that
    # the file names are a bit nicer to read
}

# Indentation modified for readability
for election in "${elections[@]}"; do
for model in "${models[@]}"; do

    file_label=$(generate_file_label \
        "$election" \
        "$model" \
        "$bloc_order" \
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

    # --time= --mem=
    #  Acceptable time formats include "minutes", "minutes:seconds", "hours:minutes:seconds", "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".
    # This output will be of the form "Submitted batch job 123456"
    if [ $model == "IAC" ]; then
        mem="100G"
        time="02-00:00:00"
    else
        mem="5G"
        time="01-00:00:00"
    fi
    job_output=$(sbatch --job-name=${job_name} \
            --mem=$mem\
            --time=$time\
            --output="${log_file}" \
            --error="${log_file}" \
            $running_script_name \
                "$election" \
                "$model" \
                "$bloc_order" \
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