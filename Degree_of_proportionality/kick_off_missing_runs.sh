#!/bin/bash

# for missing_params in "0.5 0.85 0.25 slate-BT XX-dif" \
# "0.5 0.75 0.25 slate-PL UU" \
# "0.5 0.75 0.25 slate-PL UX" \
# "0.6 0.95 0.35 slate-BT UU" \
# "0.6 0.95 0.35 slate-BT UX" \
# "0.6 0.95 0.35 slate-BT XX-same" \
# "0.6 0.95 0.35 slate-BT XX-dif" \
# "0.7 0.65 0.15 slate-CS-C XX-dif" \
# "0.7 0.5 0.35 slate-PL UU" \
# "0.7 0.5 0.35 slate-PL UX" \
# "0.8 0.95 0.45 slate-PL XX-same" \
# "0.8 0.95 0.45 slate-PL XX-dif" \
# "0.85 0.75 0.95 slate-CS-W UX" \
# "0.85 0.75 0.95 slate-CS-W XX-same" \
# "0.85 0.75 0.95 slate-CS-W XX-dif" \
# "0.85 0.7 0.05 slate-BT UX" \
# "0.9 0.6 0.05 slate-CS-C UU" \
# "0.9 0.6 0.05 slate-CS-C UX" \
# "0.9 0.6 0.05 slate-CS-C XX-same" \
# "0.9 0.6 0.05 slate-CS-C XX-dif" \
# "0.9 0.8 0.65 slate-CS-C XX-dif" \
# "0.9 0.6 0.05 slate-PL UU" \
# "0.9 0.6 0.05 slate-PL UX" \
# "0.9 0.6 0.05 slate-PL XX-same" \
# "0.9 0.6 0.05 slate-PL XX-dif" \
# "0.95 0.65 0.35 slate-CS-W XX-same"; do

for missing_params in '0.5 0.8 0.05 slate-CS-W XA' \
'0.55 0.5 0.75 slate-CS-C AX' \
'0.55 0.5 0.75 slate-CS-C X' \
'0.55 0.5 0.75 slate-PL U' \
'0.55 0.5 0.75 slate-PL XB' \
'0.6 0.6 0.05 slate-CS-C XA' \
'0.6 0.65 0.95 slate-CS-W BX' \
'0.6 0.65 0.95 slate-CS-W AX' \
'0.65 0.95 0.65 slate-BT BX' \
'0.7 0.6 0.55 slate-CS-W U' \
'0.85 0.75 0.45 slate-CS-C U'; do

sbatch -J "missing run" single_missing_run.sh $missing_params
done