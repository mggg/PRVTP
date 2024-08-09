This folder contains code and data for computing DOP from waterfall plots.

- BT_coh_to_fpv.py converts a BT coh parameter to first-place votes
- *_2_bloc_stv.py are files that generate a profile from 2 blocs, either from Dirichlet or fixed intervals
- *.sh are cluster files for running large batches of *_2_bloc_stv.py
- *.ipynb are files for generating waterfall plots and computing slopes of cones and lines of best fit.
- slope_data contains slope tables from waterfall plots

To regenerate waterfall figs, will need to unzip the election_results file. Sorry that it isn't in a smarter format, future users.