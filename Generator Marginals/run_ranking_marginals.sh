#!/bin/bash
list1=("BradleyTerry" "PlackettLuce" "SlatePreference" "DeliberativeVoter")
list2=("uniform" "strong")
list3=(2)


for item1 in "${list1[@]}"; do
    for item2 in "${list2[@]}"; do
        for item3 in "${list3[@]}"; do
            python exploring_ranking_marginals.py $item1 $item2 $item3 > "ranking_marginals_results/${item1}_${item2}_n_${item3}_results.txt"
        done
    done
done
