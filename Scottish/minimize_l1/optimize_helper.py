from votekit import PreferenceProfile, Ballot, PreferenceInterval
from swap_distance import profile_to_bloc_ballot_type
from votekit import Ballot, PreferenceProfile
from collections import Counter
import math

def l1_histograms(obs_vec_1, obs_vec_2, round_up = False, round_down = False):
    """
    Compute abs value of l1 distance between two observation vectors. 
    Will convert obs vec to counts and then compute l1.
    
    """
    if round_up:
        obs_vec_1 = [math.ceil(x) for x in obs_vec_1]
        obs_vec_2 = [math.ceil(x) for x in obs_vec_2]
    
    if round_down:
        obs_vec_1 = [math.floor(x) for x in obs_vec_1]
        obs_vec_2 = [math.floor(x) for x in obs_vec_2]

    counts_1 = Counter(obs_vec_1)
    counts_2 = Counter(obs_vec_2)
    l1 = 0

    for k, count in counts_1.items():
        if k in counts_2:
            l1 += abs(count -counts_2[k])
            counts_2.pop(k)
        else:
            l1 += count

    for k, count in counts_2.items():
        l1 += count

    return l1

def l1_slate_profiles(pp_1, pp_2, cand_to_bloc):
    """
    Compute the slate l1 distance between two profiles with named ballots.
    First converts profiles to slate type, then does l1

    Arguments:
        pp_1 (votekit.PreferenceProfile)
        pp_2 (votekit.PreferenceProfile)
        cand_to_bloc (dict): a dictionary with keys = candidates and values = bloc assignment.


    Returns:
        l1 (float): l1 distance

    """

    pp_1_dict = profile_to_bloc_ballot_type(pp_1, cand_to_bloc)
    pp_2_dict = profile_to_bloc_ballot_type(pp_2, cand_to_bloc)
    l1=0

    for ballot, weight in pp_1_dict.items():
        if ballot in pp_2_dict:
            l1 += abs(weight - pp_2_dict[ballot])
            pp_2_dict.pop(ballot)
        else:
            l1 += weight
    
    for ballot, weight in pp_2_dict.items():
        l1 +=  weight

    return l1

def generate_solid_profile(pi_b, num_ballots, cand_to_bloc):
    """
    Generate a profile of solid A over B or B over A ballots with proportion of B over A = pi_b

    Arguments:
        pi_b (float): proportion of ballots to be B over A
        num_ballots (int): number of ballots to generate
        cand_to_bloc (dict): cand to bloc, assumes blocs are A,B

    Returns:
        votekit.PreferenceProfile
    """
    solid_a_ballot = Ballot([{c} for c,b in cand_to_bloc.items() if b == "A"]+[{c} for c,b in cand_to_bloc.items() if b == "B"], 
                                    weight=int((1-pi_b)*num_ballots))
    solid_b_ballot = Ballot([{c} for c,b in cand_to_bloc.items() if b == "B"]+[{c} for c,b in cand_to_bloc.items() if b == "A"], 
                            weight=int(pi_b*num_ballots))
    
    return PreferenceProfile(ballots= [solid_a_ballot,solid_b_ballot])
