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
fpv_b = float(arguments[4])
fpv_a = float(arguments[5])
b_prop = float(arguments[6])
g = arguments[7]
pi_type = arguments[8]

# so really want b_coh to be expected FPV; for s-BT we need to compute b_coh from this
if "BT" in g:
    b_coh = slate_BT_fpv_to_coh(N_CANDS_PER_BLOC, N_CANDS_PER_BLOC, fpv_b)
    a_coh = slate_BT_fpv_to_coh(N_CANDS_PER_BLOC, N_CANDS_PER_BLOC, fpv_a)
else:
    b_coh = fpv_b
    a_coh = fpv_a


print(arguments)


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

# uniform support for AA, AB, BA, AB
if pi_type == "UU":
    pref_intervals_by_bloc = {"A": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                            "B": PreferenceInterval({f"B{i}": 1/n_cands_B for i in range(n_cands_B)})},
                                    "B": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                            "B": PreferenceInterval({f"B{i}": 1/n_cands_B for i in range(n_cands_B)})}}
    
# only BB is strong
elif pi_type == "UX":
    pref_intervals_by_bloc = {"A": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                            "B": PreferenceInterval({f"B{i}": 1/n_cands_B for i in range(n_cands_B)})},
                              "B": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                    "B": PreferenceInterval({f"B{i}": 10/(n_cands_B+9) if i == 0 
                                                             else 1 / (n_cands_B + 9) for i in range(n_cands_B)})}}
    
# AB and BB are strong for same candidate
elif pi_type == "XX-same":
    pref_intervals_by_bloc = {"A": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                    "B": PreferenceInterval({f"B{i}": 10/(n_cands_B+9) if i == 0 
                                                             else 1 / (n_cands_B + 9) for i in range(n_cands_B)})},
                              "B": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                    "B": PreferenceInterval({f"B{i}": 10/(n_cands_B+9) if i == 0 
                                                             else 1 / (n_cands_B + 9) for i in range(n_cands_B)})}}
    
# AB and BB strong for dif candidates
elif pi_type == "XX-dif":
    pref_intervals_by_bloc = {"A": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                    "B": PreferenceInterval({f"B{i}": 10/(n_cands_B+9) if i == 1
                                                             else 1 / (n_cands_B + 9) for i in range(n_cands_B)})},
                              "B": {"A": PreferenceInterval({f"A{i}": 1/n_cands_A for i in range(n_cands_A)}),
                                    "B": PreferenceInterval({f"B{i}": 10/(n_cands_B+9) if i == 0 
                                                             else 1 / (n_cands_B + 9) for i in range(n_cands_B)})}}
else:
    raise ValueError(f"{pi_type} not valid pi_type")

    

if g == "slate-CS-W":
    generator = bg.CambridgeSampler(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                cohesion_parameters=cohesion,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                slate_to_candidates=slate_to_candidates,
                                W_bloc = "B",
                                C_bloc = "A")

elif g == "slate-CS-C":
    generator = bg.CambridgeSampler(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                cohesion_parameters=cohesion,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                slate_to_candidates=slate_to_candidates,
                                W_bloc = "A",
                                C_bloc = "B")  
            
elif g == "slate-BT":
    generator = bg.slate_BradleyTerry(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                cohesion_parameters=cohesion,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                slate_to_candidates=slate_to_candidates)
    
    
            
elif g == "slate-PL":
    generator = bg.slate_PlackettLuce(candidates = slate_to_candidates["A"] + slate_to_candidates["B"],
                                bloc_voter_prop = bloc_props,
                                cohesion_parameters=cohesion,
                                pref_intervals_by_bloc = pref_intervals_by_bloc,
                                slate_to_candidates=slate_to_candidates)
    
else:
    raise ValueError(f"{g} is not valid generator")
    
# path_name = f'profiles/2_bloc/fixed_intervals/trials_{N_TRIALS}_ballots_{N_BALLOTS}_seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}'
# path = Path(path_name)
# # Create the directory
# path.mkdir(parents=True, exist_ok=True)


for i in range(N_TRIALS):
    if g == "slate-BT" and 2*N_CANDS_PER_BLOC >=12:
        pp = generator.generate_profile(number_of_ballots=num_ballots, deterministic = False)
    else:
        pp = generator.generate_profile(number_of_ballots=num_ballots)

    B_borda_shares[i] = float(score_share(pp, [2*N_CANDS_PER_BLOC-i for i in range(2*N_CANDS_PER_BLOC)], slate_to_candidates["B"]))
    f_place_votes[i] = float(score_share(pp, [1]+[0 for i in range(2*N_CANDS_PER_BLOC-1)], slate_to_candidates["B"]))

    # with open(f'{path_name}/b_coh_{b_coh}_a_coh_{a_coh}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_trial_{i}.pkl', 'wb') as file:
    #     pickle.dump(pp.to_dict(), file)

    election = STV(profile= pp,
        transfer = fractional_transfer,
        seats = N_SEATS,
        quota = "droop",
        ballot_ties = False,
        tiebreak = "random",
    )
    results = election.run_election()
    winners= [c for s in results.winners() for c in s]
    num_B_winners[i] = len([c for c in winners if "B" in c])
    
df  = pd.DataFrame({"B cands elected":num_B_winners, "B Borda shares": B_borda_shares, "B fpv": f_place_votes})


path_name = f'election_results/2_bloc/fixed_intervals/trials_{N_TRIALS}_ballots_{N_BALLOTS}_seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}'
path = Path(path_name)
# Create the directory
path.mkdir(parents=True, exist_ok=True)
df.to_csv(f"{path_name}/fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}.csv")
        
print("done")