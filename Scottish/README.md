This folder contains code for Scottish election verification.

- *bloc_opt.sh files optimize different ballot generators via wasserstein distance to the real scottish elections. These are cluster files.
- record_scottish_distance.py computes swap distances for real scottish elections
- checking_proportionality.ipynb runs STV on the scottish profiles and checks agaisnt borda/fpv for proportionality
- swap_distance.py is helper functions for computing swap distance
- optimize_helper.py is helper functions for *bloc_opt.sh
- histograms.ipynb makes swap distance hists for scottish elections
- bubble_plots.ipynb makes bubble plots for optimized profiles and scottish elections
- mds_plots_optimized_models.ipynb makes MDS plots for optimized profiles and scottish elections