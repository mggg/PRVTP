from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import generate_solid_profile, l1_histograms
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

models = {"s-BT": bg.slate_BradleyTerry,
            "s-PL": bg.slate_PlackettLuce,
            "CS-C": bg.CambridgeSampler,
            "CS-W": bg.CambridgeSampler,
            "SB": 0,
            "IC":bg.ImpartialCulture,
            "IAC": bg.ImpartialAnonymousCulture}


# optimize!
dist_dict = {}
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

dist_dict[f"{ward_label} real"] = scot_data
slate_to_candidates = {"A":[], "B":[]}
for c, b in cand_to_bloc.items():
    slate_to_candidates[b].append(c)


if model not in ["IC", "IAC"]:
    opt_stat = []
    settings_vector = []
    for pi_a in np.linspace(.51, .99, 20):
        for pi_b in np.linspace(.51, .99, 20):
            for b_prop in np.linspace(.01, .99, 20):
                settings = (pi_a, pi_b, b_prop)
                settings_vector.append(settings)
                bloc_voter_prop = {"A": 1-b_prop, "B": b_prop}
            
                cohesion_parameters = {"A": {"A": pi_a, "B": 1-pi_a},
                                        "B": {"B": pi_b, 
                                            "A": 1-pi_b}}
                
                # these are arbitrary; if slate model, ballot type not determined by PrefInt
                alphas = {"A": {"A": 1, "B": 1},
                            "B": {"B": 1, "A": 1}}
                
                if model not in ["SB"]:
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

                elif model == "SB":
                    pass
                
                else:
                    raise ValueError("invalid model string")

                # use MCMC sampling if cannot compute PDF
                
                if sum(bloc_to_cand_num.values()) >= 12 and model == "n-BT":
                    profile  = bg.generate_profile_MCMC(MCMC_sample_size)
                    
                
                elif sum(bloc_to_cand_num.values()) >= 12 and model == "s-BT":
                    profile  = bg.generate_profile(MCMC_sample_size, deterministic = False)
                

                elif model == "SB":
                    profile = generate_solid_profile(b_prop, int(scottish_profile.total_ballot_wt), cand_to_bloc)
                    
                else:
                    profile  = bg.generate_profile(int(scottish_profile.total_ballot_wt))
                
                distances = dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
                dist_dict[settings] = distances

                l1 = l1_histograms(distances, dist_dict[f"{ward_label} real"], round_down=True)
                opt_stat.append(l1)

    min_settings = settings_vector[np.argmin(opt_stat)]

    
  
else:
    g = models[model](candidates = list(cand_to_bloc.keys()))
    profile = g.generate_profile(int(scottish_profile.total_ballot_wt))
    
    distances = dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
    l1 = l1_histograms(distances, dist_dict[f"{ward_label} real"], round_down=True)
    opt_stat = [l1]

    dist_dict["N/A"] = dist_profile_to_solid(profile, cand_to_bloc, bloc_order)
    min_settings = "N/A"
 


with open(f"data/2_bloc/{ward_label}_two_bloc_optimized_l1_{model}_bloc_order_{bloc_order}_b_bloc_parties_{b_bloc_parties}.pickle", "wb") as f:
    # min settings, min l1, distances_model, distances_scottish
    print(min_settings)
    pickle.dump((min_settings, np.min(opt_stat), dist_dict[min_settings], dist_dict[f"{ward_label} real"]),f)