This folder contains code for Scottish election verification.

- *bloc_opt.sh files optimize different ballot generators via l1 distance of swap distributions to the real scottish elections swap distributions. These are cluster files.
- checking_proportionality.ipynb runs STV on the scottish profiles and checks agaisnt borda/fpv for proportionality
- swap_distance.py is helper functions for computing swap distance
- optimize_helper.py is helper functions for *bloc_opt.sh
- bubble_plots*.ipynb makes bubble plots for optimized profiles and scottish elections
