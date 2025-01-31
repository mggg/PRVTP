#!/bin/bash

for missing_params in \
'0.55 0.85 0.35 slate-PL XXdif' \
'0.55 0.85 0.45 slate-BT UU' \
'0.55 0.85 0.45 slate-BT UX' \
'0.55 0.85 0.45 slate-BT XXsame'; do

sbatch -J "missing run" single_missing_run.sh $missing_params
done