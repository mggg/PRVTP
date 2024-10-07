from votekit import PreferenceInterval
import numpy as np
from random import shuffle

def assign_cand_names(interval: PreferenceInterval, cand_index_list: list[tuple[str, int]]):
    """
    Given a preference interval, sort the probabilities from high to low and remove the candidate
    labels. Assign any candidate name to the index provided in cand_index_list.
    Uniformly assign remaining candidates. 

    Eg (Brantley: 1/2, Chris:1/6 Will:1/3) and (Chris, 0) would assign Chris to 1/2 and will and
    Brantley at random. 

    Args:
        interval (PreferenceInterval): PrefInterval to relabel.
        cand_index_list (list[tuple[str, int]]): List of cand, index pairs. Index starts from 0 for
            highest probability.

    Returns:
        PreferenceInterval: interval with relabeling
    
    """
    # errors to raise
    # check that cands_to_change is subset of all_cands, no repeated names
    # no repeated indices 

    all_candidates = list(interval.candidates)
    probs = list(interval.interval.values())+ [0 for _ in range(len(interval.zero_cands))]
    probs.sort(reverse=True)

    remaining_probs = probs.copy() 


    new_interval_dict = {c:0 for c in all_candidates}

    for c, i in cand_index_list:
        new_interval_dict[c] = probs[i]
        remaining_probs.remove(probs[i])
    
    shuffle(remaining_probs)
    
    cands_to_change, _ = zip(*cand_index_list)
    remaining_cands = set(all_candidates).difference(cands_to_change)

    for i, c in enumerate(remaining_cands):
        new_interval_dict[c] = remaining_probs[i]

    return PreferenceInterval(new_interval_dict)




# #### tests
# p_int = PreferenceInterval({"Chris": 1/2, "Will": 1/3, "Brantley":1/6, "Yang": 0, "Me": 0})

# new_p_int = assign_cand_names(p_int, [("Chris", 0)])
# print("Chris to 0", new_p_int, "zero cands", new_p_int.zero_cands)

# new_p_int = assign_cand_names(p_int, [("Chris", 1)])
# print("Chris to 1", new_p_int, "zero cands", new_p_int.zero_cands)

# new_p_int = assign_cand_names(p_int, [("Chris", -1)])
# print("Chris to -1", new_p_int, "zero cands", new_p_int.zero_cands)


# new_p_int = assign_cand_names(p_int, [("Chris", -1), ("Yang", 0)])
# print("Chris to -1, yang to 0", new_p_int, "zero cands", new_p_int.zero_cands)

# new_p_int = assign_cand_names(p_int, [("Chris", -1), ("Yang", 1)])
# print("Chris to -1, yang to 1", new_p_int, "zero cands", new_p_int.zero_cands)