import votekit.ballot_generator as bg
from votekit.elections import STV, fractional_transfer
import pickle
from votekit.pref_interval import PreferenceInterval
import sys
import pandas as pd
from scipy.optimize import fsolve
from functools import partial
from pathlib import Path
from BT_coh_to_fpv import slate_BT_fpv_to_coh
from helper import assign_cand_names

def score_share(profile, score_vector, candidate_subset):
    """
    Returns the score share of the candidate subset.
    Assumes all ballots are untied.
    """
    total_score = sum(sum(score_vector[:len(b.ranking)])*b.weight for b in profile.ballots)
    share = 0
    for ballot in profile.ballots:
        for s in ballot.ranking:
            if len(s) > 1:
                raise TypeError("All ballots must be untied.")

        share += sum([score_vector[i] for i,s in enumerate(ballot.ranking) for c in s if c in candidate_subset])

    return(share/total_score)
        


arguments = sys.argv[1:]
N_TRIALS = int(arguments[0])
N_BALLOTS = int(arguments[1])
N_SEATS = int(arguments[2])
N_CANDS_PER_BLOC = int(arguments[3])
strong_dirichlet = float(arguments[4])
uniform_dirichlet = float(arguments[5])
fpv_b = float(arguments[6])
fpv_a = float(arguments[7])
b_prop = float(arguments[8])
g = str(arguments[9])
pi_type = str(arguments[10])


print(arguments)

# so really want b_coh to be expected FPV; for s-BT we need to compute b_coh from this
if "BT" in g:
    b_coh = slate_BT_fpv_to_coh(N_CANDS_PER_BLOC, N_CANDS_PER_BLOC, fpv_b)
    a_coh = slate_BT_fpv_to_coh(N_CANDS_PER_BLOC, N_CANDS_PER_BLOC, fpv_a)
else:
    b_coh = fpv_b
    a_coh = fpv_a



n_cands_A = N_CANDS_PER_BLOC
n_cands_B = N_CANDS_PER_BLOC
slate_to_candidates = {"A": [f"A{i}" for i in range(n_cands_A)],
                        "B": [f"B{i}" for i in range(n_cands_B)]}
cohesion = {"A":{"A": a_coh, "B":1-a_coh}, "B":{"A": 1-b_coh, "B":b_coh}}
bloc_props = {"A": 1-b_prop, "B": b_prop}
num_ballots = N_BALLOTS

num_B_winners = [-1]* N_TRIALS
B_borda_shares = [-1]* N_TRIALS
f_place_votes = [-1]*N_TRIALS


# uniform support for all
if pi_type == "UU":
    alphas = {"A": {"A": uniform_dirichlet, "B": uniform_dirichlet},
            "B":{"A": uniform_dirichlet, "B": uniform_dirichlet}}
    
# strong for BB, unif else
elif pi_type == "UX":
    alphas = {"A": {"A": uniform_dirichlet, "B": uniform_dirichlet},
            "B":{"A": uniform_dirichlet, "B": strong_dirichlet}}
    
# strong AB and BB, unif else, agree in strong
elif pi_type == "XXsame":
    alphas = {"A": {"A": uniform_dirichlet, "B": strong_dirichlet},
            "B":{"A": uniform_dirichlet, "B": strong_dirichlet}}
    
# strong AB and BB, unif else, no enforced agree in strong
elif pi_type == "XXdif":
    alphas = {"A": {"A": uniform_dirichlet, "B": strong_dirichlet},
            "B":{"A": uniform_dirichlet, "B": strong_dirichlet}}


pref_intervals_by_bloc = {"A": {"A":PreferenceInterval.from_dirichlet(slate_to_candidates["A"], alphas["A"]["A"]), 
                                    "B":PreferenceInterval.from_dirichlet(slate_to_candidates["B"], alphas["A"]["B"])},
                              "B": {"A":PreferenceInterval.from_dirichlet(slate_to_candidates["A"], alphas["B"]["A"]), 
                                    "B":PreferenceInterval.from_dirichlet(slate_to_candidates["B"], alphas["B"]["B"])}}

# strong alignment
if pi_type == "XXsame":
    pref_intervals_by_bloc["A"]["B"] = assign_cand_names(pref_intervals_by_bloc["A"]["B"], [("B0",0)])
    pref_intervals_by_bloc["B"]["B"] = assign_cand_names(pref_intervals_by_bloc["B"]["B"], [("B0",0)])





"""
# # uniform support for all
# if pi_type == "U":
#     alphas = {"A": {"A": uniform_dirichlet, "B": uniform_dirichlet},
#             "B":{"A": uniform_dirichlet, "B": uniform_dirichlet}}
    
# # strong for B cands, unif for A cands
# elif pi_type == "XB":
#     alphas = {"A": {"A": uniform_dirichlet, "B": strong_dirichlet},
#             "B":{"A": uniform_dirichlet, "B": strong_dirichlet}}
    
# # strong for A cands, unif for B cands
# elif pi_type == "XA":
#     alphas = {"A": {"A": strong_dirichlet, "B": uniform_dirichlet},
#             "B":{"A": strong_dirichlet, "B": uniform_dirichlet}}
    
# # B has strong pref, A has unif
# elif pi_type == "BX":
#     alphas = {"A": {"A": uniform_dirichlet, "B": uniform_dirichlet},
#             "B":{"A": strong_dirichlet, "B": strong_dirichlet}}

# # A has strong pref, B has unif
# elif pi_type == "AX":
#     alphas = {"A": {"A": strong_dirichlet, "B": strong_dirichlet},
#             "B":{"A": uniform_dirichlet, "B": uniform_dirichlet}}

# # B has strong pref, A has strong pref
# elif pi_type == "X":
#     alphas = {"A": {"A": strong_dirichlet, "B": strong_dirichlet},
#             "B":{"A": strong_dirichlet, "B": strong_dirichlet}}
"""



if g == "slate-PL":
    generator = bg.slate_PlackettLuce(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                cohesion_parameters=cohesion,
                                slate_to_candidates=slate_to_candidates)
    
    
            
elif g == "slate-BT":
    generator = bg.slate_BradleyTerry(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                cohesion_parameters=cohesion,
                                slate_to_candidates=slate_to_candidates)
    
    
elif g == "slate-CS-W":
    generator = bg.CambridgeSampler(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                cohesion_parameters=cohesion,
                                slate_to_candidates=slate_to_candidates,
                                W_bloc = "B",
                                C_bloc = "A")
elif g == "slate-CS-C":
    generator = bg.CambridgeSampler(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                cohesion_parameters=cohesion,
                                slate_to_candidates=slate_to_candidates,
                                W_bloc = "A",
                                C_bloc = "B")
else:
    raise ValueError(f"{g} is not valid generator")
    
# path_name = f'profiles/2_bloc/dirichlet/trials_{N_TRIALS}_ballots_{N_BALLOTS}_seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}'
# path = Path(path_name)
# # Create the directory
# path.mkdir(parents=True, exist_ok=True)


for i in range(N_TRIALS):
    if g == "slate-BT" and 2*N_CANDS_PER_BLOC >12:
        pp = generator.generate_profile(number_of_ballots=num_ballots, deterministic = False)
    else:
        pp = generator.generate_profile(number_of_ballots=num_ballots)

    B_borda_shares[i] = float(score_share(pp, [2*N_CANDS_PER_BLOC-i for i in range(2*N_CANDS_PER_BLOC)], slate_to_candidates["B"]))
    f_place_votes[i] = float(score_share(pp, [1]+[0 for i in range(2*N_CANDS_PER_BLOC-1)], slate_to_candidates["B"]))


    # with open(f'{path_name}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}_trial_{i}.pkl', 'wb') as file:
    #     pickle.dump(pp.to_dict(), file)

    election = STV(profile= pp,
        m = N_SEATS,
        simultaneous = True,
        tiebreak = "random",
    )
    
    winners= [c for s in election.get_elected(-1) for c in s]
    num_B_winners[i] = len([c for c in winners if "B" in c])
    
df  = pd.DataFrame({"B cands elected":num_B_winners, "B Borda shares": B_borda_shares, "B fpv": f_place_votes})


path_name = f'election_results/2_bloc/dirichlet/trials_{N_TRIALS}_ballots_{N_BALLOTS}_seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}'
path = Path(path_name)
# Create the directory
path.mkdir(parents=True, exist_ok=True)
df.to_csv(f"{path_name}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}.csv")
        
print("done")