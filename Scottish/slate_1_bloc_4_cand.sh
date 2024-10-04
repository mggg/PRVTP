#!/bin/bash



elections=("aberdeen 2017 11" "aberdeen 2022 11" "aberdeen 2017 10")
# elections=("aberdeen 2022 11" "aberdeen 2017 10")
# elections=("aberdeen 2017 11")

models=("IC" "IAC" "CS-W" "CS-C" "SB" "s-PL" "n-PL" "s-BT" "n-BT")
# models=("CS-W")

bloc_order="AB"



for election in "${elections[@]}"; do
for model in "${models[@]}"; do
    echo "Running $election $model $bloc_order"
    python slate_1_bloc_optimize.py "${election}" $model $bloc_order > "./LOGS/slate_1_bloc_optimize_${election}_${model}_${bloc_order}.log" 2>&1 &
done
done


