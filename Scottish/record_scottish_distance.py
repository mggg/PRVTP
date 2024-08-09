from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import estimate_1_bloc_parameters, generate_solid_profile
from votekit.cvr_loaders import load_scottish
import numpy as np
from votekit import PreferenceInterval, Ballot
from scipy.stats import wasserstein_distance
import votekit.ballot_generator as bg
import pickle

args = sys.argv[1:]
print("args", args)
bloc_order = str(args[0])


b_bloc_parties = ["SLP", "SG", "SLD", "TUSC", "GF"]
file_names = {"fife 2022 21": "../election_data/fife_2022_ward21.csv",
              "aberdeen 2017 12" : "../election_data/aberdeen_2017_ward12.csv",
              "aberdeen 2022 12": "../election_data/aberdeen_2022_ward12.csv",
              "angus 2012 8": "../election_data/angus_2012_ward8.csv",
              "falkirk 2017 6": "../election_data/falkirk_2017_ward6.csv",
              "clackmannanshire 2012 2": "../election_data/clackmannanshire_2012_ward2.csv",
              "renfrewshire 2017 1": "../election_data/renfrewshire_2017_ward1.csv",
              "glasgow 2012 16": "../election_data/glasgow_2012_ward16.csv",
              "north-ayrshire 2022 1": "../election_data/north_ayrshire_2022_north_coast.csv"
              }

for election in file_names:
    city, year, ward = election.split(" ")
    ward_label = f"{city} ward_{ward} {year}"

    scottish_profile, num_seats = load_scottish(file_names[election])
    cand_to_bloc = {c:"B" if c.replace("'","").split(",")[2].strip(")").strip(" ") in b_bloc_parties 
                    else "A" for c in scottish_profile.candidates}

    # count the number of candidates in each bloc
    bloc_to_cand_num = {"A": len([c for c, bloc in cand_to_bloc.items() if bloc == "A"]),
                        "B": len([c for c, bloc in cand_to_bloc.items() if bloc == "B"])}

    scot_data = dist_profile_to_solid(scottish_profile, cand_to_bloc, bloc_order)

    # once compute optimal pi_b, save that pi_b and the corresponding distances to solid
    with open(f"distance_data/scot/distance_to_solid_{ward_label}_real_profile_bloc_order_{bloc_order}.pickle", "wb") as f:
        pickle.dump(scot_data,f)
