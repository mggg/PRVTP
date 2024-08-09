from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import estimate_1_bloc_parameters, generate_solid_profile
from votekit.cvr_loaders import load_scottish
import numpy as np
from votekit import PreferenceInterval, Ballot
from scipy.stats import wasserstein_distance, kstest
import votekit.ballot_generator as bg
import pickle

args = sys.argv[1:]
print("args", args)
election = str(args[0])
model = str(args[1])
bloc_order = str(args[2])

optimize_for ="WD" #"KS" #WD

MCMC_sample_size = 10000

if election in ["glasgow 2012 16", "north-ayrshire 2022 1"] and model == "s-BT":
    print("lowered pi_b coarse for time reasons")
    pi_b_coarse = 10
else:
    pi_b_coarse = 50

b_bloc_parties = ["Scottish National Party (SNP)", "Green (Gr)"]

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
            "SB": 0,
            "IC":bg.ImpartialCulture,
            "IAC": bg.ImpartialAnonymousCulture}

# estimate model parameters
model_parameters = estimate_1_bloc_parameters(file_names[election], b_bloc_parties)

# optimize!
data_dict = {}
wass_dict = {}

city, year, ward = election.split(" ")
ward_label = f"{city} ward_{ward} {year}"


scottish_profile, num_seats, cand_list, cand_to_party, ward = load_scottish(file_names[election])
cand_to_bloc = {c:"B" if cand_to_party[c] in b_bloc_parties 
                else "A" for c in cand_list}

# count the number of candidates in each bloc
bloc_to_cand_num = {"A": len([c for c, bloc in cand_to_bloc.items() if bloc == "A"]),
                    "B": len([c for c, bloc in cand_to_bloc.items() if bloc == "B"])}

scot_data = dist_profile_to_solid(scottish_profile, cand_to_bloc, bloc_order)

data_dict[f"{ward_label} real"] = scot_data

# try a one bloc model, where cohesion is percentage of first place votes
slate_to_candidates = {b: [f"{b}_{i}" for i in range(bloc_to_cand_num[b])] for b in bloc_to_cand_num.keys()}
cand_to_bloc = {c:b for b,c_list in slate_to_candidates.items() for c in c_list}

# only looking at B bloc
bloc_voter_prop = {"A": 0, "B": 1}

if model not in ["IC", "IAC"]:
    lower = .01
    upper = .99
    for scale in [.1, .01, .001]:
        opt_stat = []
        pi_b_vector = []
        for pi_b in np.linspace(lower, upper, pi_b_coarse):
            pi_b_vector.append(pi_b)

            # A bloc does not matter here
            cohesion_parameters = {"A": {"A": 1, "B": 0},
                                    "B": {"B": pi_b, 
                                        "A": 1-pi_b}}
            
            # these are arbitrary; if slate model, ballot type not determined by PrefInt
            # if name model, we use estimated PrefInt
            alphas = {"A": {"A": 1, "B": 1},
                        "B": {"B": 1, "A": 1}}
            
            if model not in ["n-BT", "n-PL", "SB"]:
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
            elif model != "SB":
                candidates = []
                for c_list in slate_to_candidates.values():
                    candidates += c_list

                ba_interval = {f"A_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["A"].values())}
                bb_interval = {f"B_{i}":p for i, p in enumerate(model_parameters["pref_intervals"]["B"].values())}

                # A pref intervals don't matter because only looking at B bloc voters
                pref_intervals_by_bloc = {"A": {"A": PreferenceInterval({c: 1/len(slate_to_candidates["A"]) for c in slate_to_candidates["A"]}),
                                                "B": PreferenceInterval({c: 1/len(slate_to_candidates["B"]) for c in slate_to_candidates["B"]})},
                                        "B": {"A" : PreferenceInterval(ba_interval),
                                                "B" : PreferenceInterval(bb_interval)}
                                        }
                bg = models[model](candidates = candidates, cohesion_parameters = cohesion_parameters, bloc_voter_prop = bloc_voter_prop,
                        pref_intervals_by_bloc = pref_intervals_by_bloc)

            elif model == "SB":
                pass
            
            else:
                raise ValueError("invalid model string")

            # use MCMC sampling if cannot compute PDF
            
            if sum(bloc_to_cand_num.values()) >= 12 and model == "n-BT":
                profile  = bg.generate_profile_MCMC(MCMC_sample_size)
                distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
                    
            elif model == "SB":
                solid_profile = generate_solid_profile(pi_b, int(scottish_profile.num_ballots()), bloc_to_cand_num)
                solid_cand_to_bloc = {f"{b}_{i}": b for b in ["A", "B"] for i in range(bloc_to_cand_num[b]) }
                distances = dist_profile_to_solid(solid_profile, solid_cand_to_bloc, bloc_order)
            else:
                profile  = bg.generate_profile(int(scottish_profile.num_ballots()))
                distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
        
            data_dict[f"pi_b {pi_b}"] = distances

            if optimize_for == "WD":
                wd = wasserstein_distance(scot_data, distances)
                opt_stat.append(wd)

            elif optimize_for == "KS":
                ks = kstest(scot_data, distances)
                opt_stat.append(ks.statistic)
        
        
        min_pi_b = pi_b_vector[np.argmin(opt_stat)]

        lower = min_pi_b - scale*.5
        upper = min_pi_b + scale*.5

else:
    print(model)
    g = models[model](candidates = list(cand_to_bloc.keys()))
    print(g)
    profile = g.generate_profile(int(scottish_profile.num_ballots()))
    distances =  dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
    data_dict[f"pi_b N/A"] = distances
    min_pi_b = "N/A"

# once compute optimal pi_b, save that pi_b and the corresponding distances to solid
with open(f"distance_data/1_bloc/distance_to_solid_{ward_label}_one_bloc_optimized_{optimize_for}_{model}_bloc_order_{bloc_order}_b_bloc_parties_{b_bloc_parties}.pickle", "wb") as f:
    pickle.dump((min_pi_b, data_dict[f"pi_b {min_pi_b}"]),f)
