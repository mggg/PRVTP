from votekit.elections import STV, Borda
import pickle
import sys, csv
from pathlib import Path
import numpy as np



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

num_B_winners_STV = [-1]* N_TRIALS
num_B_winners_borda = [-1]* N_TRIALS


profile_path_name = f'../generate_profiles/saved_profiles/2_bloc/dirichlet/seats_{N_SEATS}/cperbloc_{N_CANDS_PER_BLOC}/trials_{N_TRIALS}/ballots_{N_BALLOTS}/fpv_b_{fpv_b}/fpv_a_{fpv_a}/b_prop_{b_prop}/{g}/pi_type_{pi_type}/dunif_{uniform_dirichlet}/dstrong_{strong_dirichlet}/'


for i in range(N_TRIALS):
    with open(f'{profile_path_name}/seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}_trials_{N_TRIALS}_ballots_{N_BALLOTS}_fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}_trial_{i}.pkl', 'rb') as file:
        profile = pickle.load(file)

    stv_election = STV(profile, m=N_SEATS)
    borda_election = Borda(profile, m=N_SEATS, tiebreak = "random")

    stv_winners= [c for s in stv_election.get_elected(-1) for c in s]
    num_B_winners_STV[i] = len([c for c in stv_winners if "B" in c])

    borda_winners= [c for s in borda_election.get_elected(-1) for c in s]
    num_B_winners_borda[i] = len([c for c in borda_winners if "B" in c])

path_name = f'election_results/2_bloc/dirichlet/seats_{N_SEATS}/cperbloc_{N_CANDS_PER_BLOC}/trials_{N_TRIALS}/ballots_{N_BALLOTS}/fpv_b_{fpv_b}/fpv_a_{fpv_a}/b_prop_{b_prop}/{g}/pi_type_{pi_type}/dunif_{uniform_dirichlet}/dstrong_{strong_dirichlet}/'
path = Path(path_name)
# Create the directory
path.mkdir(parents=True, exist_ok=True)

with open(f"{path_name}/seats_{N_SEATS}_cperbloc_{N_CANDS_PER_BLOC}_trials_{N_TRIALS}_ballots_{N_BALLOTS}_fpv_b_{fpv_b}_fpv_a_{fpv_a}_b_prop_{b_prop}_{g}_pi_type_{pi_type}_dunif_{uniform_dirichlet}_dstrong_{strong_dirichlet}.csv", mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows([["avg B cands elected stv","avg B cands elected borda"],
                        [np.average(num_B_winners_STV), np.average(num_B_winners_borda)]
                        ])
print("done")
    
