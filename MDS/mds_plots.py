import votekit.ballot_generator as bg
from votekit.plots import plot_MDS, compute_MDS
from votekit.metrics import earth_mover_dist, lp_dist
from votekit import Ballot, PreferenceProfile
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys, pickle
from functools import partial
from peter_slate_emd import slate_earth_mover_dist
args = sys.argv[1:]
metric = args[0]
b_coh = float(args[1])

print(metric, b_coh)


def extend_ballots(pp: PreferenceProfile, num_cands:int):
    """
    Turn ballots of max length-1 into ballots of max length.
    Assumes no ties.

    Args:
        pp (PrefProfile): profile
        num_cands (int): total number of candidates, ie max ballot length

    Returns: 
        PreferenceProfile
    
    """

    # identify n-1 ballots with n 
    new_ballots = [Ballot() for _ in range(pp.num_ballots)]

    for i, ballot in enumerate(pp.ballots):
        for s in ballot.ranking:
            if len(s) >1:
                raise TypeError("Ballots must have no ties.")
            
        if len(ballot.ranking) == num_cands-1:
            ballot_cands = [c for s in ballot.ranking for c in s]
            missing_cand = set(pp.candidates).difference(ballot_cands)
            new_ranking = ballot.ranking +(missing_cand,)

            new_ballots[i] = Ballot(ranking = new_ranking, weight = ballot.weight)


        else:
            new_ballots[i] = ballot

    return PreferenceProfile(ballots = new_ballots, candidates = pp.candidates).condense_ballots()


pref_scenario_settings = {"U": {"A":2, "B":2 }, 
                          "X":{"A":2, "B":1/2 },
                            "Y":{"A":1/2, "B":2 },
                              "S":{"A":1/2, "B":1/2 }}

pref_scenario_markers = {"U": "$\mathdefault{U}$", 
                          "X":"$\mathdefault{X}$",
                            "Y":"$\mathdefault{Y}$",
                              "S":"$\mathdefault{S}$"}

pref_scenarios = list(pref_scenario_settings.keys())
cand_per_slate = 3
num_profiles = 10
num_ballots = 1000

bloc_voter_prop = {"A":0, "B": 1}
slate_to_candidates = {"A": [f"A_{i}" for i in range(cand_per_slate)],
                       "B": [f"B_{i}" for i in range(cand_per_slate)]}
model_to_color = {'CS-C': '#D2691E', 'CS-W': '#E32636', 's-BT': '#FFBF00', 's-PL': '#8DB600'}
models = list(model_to_color.keys())
emd_slate_to_candidates = {c: [c] for c_list in slate_to_candidates.values() for c in c_list}
profile_dict = {(m, s) :[] for m in models for s in pref_scenarios}


for pref_scenario_str, b_alphas in pref_scenario_settings.items():
    for model in models:
        if model == "CS-C":
            g = bg.CambridgeSampler.from_params(slate_to_candidates=slate_to_candidates,
                    bloc_voter_prop=bloc_voter_prop,
                    cohesion_parameters={"A": {"A": 1, "B": 0},
                                            "B": {"A":1-b_coh, "B":b_coh}},
                    alphas={"A": {"A":1, "B":1},
                            "B": b_alphas},
                    W_bloc = "A",
                    C_bloc = "B")

        elif model == "CS-W":
            g = bg.CambridgeSampler.from_params(slate_to_candidates=slate_to_candidates,
                    bloc_voter_prop=bloc_voter_prop,
                    cohesion_parameters={"A": {"A": 1, "B": 0},
                                            "B": {"A":1-b_coh, "B":b_coh}},
                    alphas={"A": {"A":1, "B":1},
                            "B": b_alphas},
                    W_bloc = "B",
                    C_bloc = "A")
        
        elif model == "s-BT":
            g = bg.slate_BradleyTerry.from_params(slate_to_candidates=slate_to_candidates,
                    bloc_voter_prop=bloc_voter_prop,
                    cohesion_parameters={"A": {"A": 1, "B": 0},
                                            "B": {"A":1-b_coh, "B":b_coh}},
                    alphas={"A": {"A":1, "B":1},
                            "B": b_alphas},)

        elif model == "s-PL":
            g = bg.slate_PlackettLuce.from_params(slate_to_candidates=slate_to_candidates,
                    bloc_voter_prop=bloc_voter_prop,
                    cohesion_parameters={"A": {"A": 1, "B": 0},
                                            "B": {"A":1-b_coh, "B":b_coh}},
                    alphas={"A": {"A":1, "B":1},
                            "B": b_alphas},)

        else:
            raise ValueError("invalid generator")
        
    
        
            
        profile_dict[(model, pref_scenario_str)] = [extend_ballots(pp= g.generate_profile(num_ballots), num_cands = 2*cand_per_slate) for _ in range(num_profiles)]



if metric == "emd":
    distance = partial(slate_earth_mover_dist, slate_dict=emd_slate_to_candidates)

elif metric == "l1":
    distance = lp_dist

coord_dict = compute_MDS(data = profile_dict,
            distance = distance, 
            )



with open(f'coords/mds_coords_{metric}_b_coh_{b_coh}.pickle', 'wb') as handle:
    pickle.dump(coord_dict, handle)

ax = plot_MDS(coord_dict=coord_dict,
                plot_kwarg_dict={(model, pref_scenario): {"c": model_to_color[model], "s":50, "marker":pref_scenario_markers[pref_scenario], "alpha" :.5} 
                                            for model in models for pref_scenario in pref_scenarios},
                legend = False, title = False)

plt.title(f"{metric.upper()} MDS b_coh = {b_coh}")
# Create a list of patches for the legend
patches = [mpatches.Patch(color=color, label=label) for label, color in model_to_color.items()]
plt.legend(handles=patches, loc='center left', bbox_to_anchor=(1, 1/2))
plt.savefig(f"Figures/mds_plot_{metric}_b_coh_{b_coh}.png", dpi = 300)
