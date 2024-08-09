from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import estimate_2_bloc_parameters, generate_solid_profile
from votekit.cvr_loaders import load_scottish
import numpy as np
from votekit import PreferenceInterval, Ballot
from scipy.stats import wasserstein_distance
import votekit.ballot_generator as bg
import pickle

args = sys.argv[1:]
print("args", args)
election = str(args[0])
model = str(args[1])
bloc_order = str(args[2])

# dist_profile_to_solid (profile, cand_to_bloc, bloc_order)

MCMC_sample_size = 10000
pi_coarse = 50

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

models = {"n-BT": bg.name_BradleyTerry,
            "n-PL": bg.name_PlackettLuce,
            "s-BT": bg.slate_BradleyTerry,
            "s-PL": bg.slate_PlackettLuce,
            "CS-C": bg.CambridgeSampler,
            "CS-W": bg.CambridgeSampler,
            "solid": 0}


# estimate model parameters
model_parameters = estimate_2_bloc_parameters(file_names[election], b_bloc_parties)

# optimize!
data_dict = {}
wass_dict = {}

city, year, ward = election.split(" ")
ward_label = f"{city} ward_{ward} {year}"

scottish_profile, num_seats = load_scottish(file_names[election])
cand_to_bloc = {c:"B" if c.replace("'","").split(",")[2].strip(")").strip(" ") in b_bloc_parties 
                else "A" for c in scottish_profile.candidates}

# count the number of candidates in each bloc
bloc_to_cand_num = {"A": len([c for c, bloc in cand_to_bloc.items() if bloc == "A"]),
                    "B": len([c for c, bloc in cand_to_bloc.items() if bloc == "B"])}

scot_data = dist_profile_to_solid(scottish_profile, cand_to_bloc, bloc_order)

data_dict[f"{ward_label} real"] = scot_data

# try a one bloc model, where cohesion is percentage of first place votes
slate_to_candidates = {b: [f"{b}_{i}" for i in range(bloc_to_cand_num[b])] for b in bloc_to_cand_num.keys()}
cand_to_bloc = {c:b for b,c_list in slate_to_candidates.items() for c in c_list}


bloc_voter_prop = {"A": model_parameters["bloc_first"]["A"], "B": model_parameters["bloc_first"]["B"]}


lower_b = .01
upper_b = .99

lower_a = .01
upper_a = .99
for scale in [.1, .01, .001]:
    wass_distances = []
    pi_vector = []
    for pi_b in np.linspace(lower_b, upper_b, pi_coarse):
        for pi_a in np.linspace(lower_a, upper_a, pi_coarse):
            pi_vector.append((pi_a,pi_b))

            
            cohesion_parameters = {"A": {"A": pi_a, "B": 1-pi_a},
                                    "B": {"B": pi_b, 
                                        "A": 1-pi_b}}
            
            # these are arbitrary; if slate model, ballot type not determined by PrefInt
            # if name model, we use estimated PrefInt
            alphas = {"A": {"A": 1, "B": 1},
                        "B": {"B": 1, "A": 1}}
            
            if model not in ["n-BT", "n-PL", "solid"]:
                if "CS" in model:
                    if model == "CS-W":
                        bg = models[model].from_params(slate_to_candidates, 
                                    bloc_voter_prop, 
                                    cohesion_parameters, 
                                    alphas,
                                    W_bloc = "B",
                                    C_bloc = "A")
                    else:
                        bg = models[model].from_params(slate_to_candidates, 
                                    bloc_voter_prop, 
                                    cohesion_parameters, 
                                    alphas,
                                    W_bloc = "A",
                                    C_bloc = "B")
                else:
                    bg = models[model].from_params(slate_to_candidates, 
                                    bloc_voter_prop, 
                                    cohesion_parameters, 
                                    alphas)
            elif model != "solid":
                candidates = []
                for c_list in slate_to_candidates.values():
                    candidates += c_list

                aa_interval = {f"A_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["A"]["A"].values())}
                ab_interval = {f"B_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["A"]["B"].values())}
                
                ba_interval = {f"A_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["B"]["A"].values())}
                bb_interval = {f"B_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["B"]["B"].values())}

                
                pref_intervals_by_bloc = {"A": {"A": PreferenceInterval(aa_interval),
                                                "B": PreferenceInterval(ab_interval)},
                                        "B": {"A" : PreferenceInterval(ba_interval),
                                                "B" : PreferenceInterval(bb_interval)}
                                        }
                bg = models[model](candidates = candidates, cohesion_parameters = cohesion_parameters, bloc_voter_prop = bloc_voter_prop,
                        pref_intervals_by_bloc = pref_intervals_by_bloc)

            elif model == "solid":
                pass
            
            else:
                raise ValueError("invalid model string")

            # use MCMC sampling if cannot compute PDF
            
            if sum(bloc_to_cand_num.values()) >= 12 and model in ["n-BT", "s-BT"]:
                if model == "n-BT":
                    profile  = bg.generate_profile_MCMC(MCMC_sample_size)
                    distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
                    
                else:
                    profile  = bg.generate_profile(MCMC_sample_size, deterministic = False)
                    distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
                    
            elif model == "solid":
                solid_profile_b = generate_solid_profile(pi_b, int(bloc_voter_prop["B"]*scottish_profile.num_ballots()), bloc_to_cand_num)
                solid_profile_a = generate_solid_profile(pi_a, int(bloc_voter_prop["A"]*scottish_profile.num_ballots()), bloc_to_cand_num)
                solid_cand_to_bloc = {f"{b}_{i}": b for b in ["A", "B"] for i in range(bloc_to_cand_num[b]) }
                distances = dist_profile_to_solid(solid_profile_a + solid_profile_b, solid_cand_to_bloc, bloc_order)
            else:
                profile  = bg.generate_profile(int(scottish_profile.num_ballots()))
                distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
        
            data_dict[f"pi_a {pi_a} pi_b {pi_b}"] = distances
            wd = wasserstein_distance(scot_data, distances)
            wass_distances.append(wd)

    
    min_w = min(wass_distances)
    min_pi_a, min_pi_b = pi_vector[wass_distances.index(min_w)]

    lower_b = min_pi_b - scale*.5
    upper_b = min_pi_b + scale*.5

    lower_a = min_pi_a - scale*.5
    upper_a = min_pi_a + scale*.5


# once compute optimal pi_b, save that pi_b and the corresponding distances to solid
with open(f"distance_data/2_bloc/distance_to_solid_{ward_label}_two_bloc_optimized_{model}_bloc_order_{bloc_order}.pickle", "wb") as f:
    pickle.dump(((min_pi_a, min_pi_b), data_dict[f"pi_a {min_pi_a} pi_b {min_pi_b}"]),f)
