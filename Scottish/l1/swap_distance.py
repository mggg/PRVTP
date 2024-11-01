import numpy as np
from votekit import Ballot, PreferenceProfile

def bloc_ballot_to_rank_encoding(bloc_type_ballot):
    """ 
    Given a bloc type ballot, convert to rank encoding. eg A>B>A becomes (3 1 | 2)

    Arguments:
        bloc_type_ballot (list[str]): list of strings represent bloc type ballot. eg ["AA", "B"]
            (with all remaining candidates tied at bottom)

    Returns:
        dict[str, list]: (bloc, rank_vector) dictionary
    """
    mult_blocs = [b for s in bloc_type_ballot for b in s]
    num_cands = len(mult_blocs)
    blocs = set(mult_blocs)
    rank_vector = list(range(num_cands, 0, -1))

    bloc_rankings = {b:[] for b in blocs}
    i = 0
    for  s in bloc_type_ballot:
        rank_points = sum(rank_vector[i:i+len(s)])/len(s)
        i += len(s)
        for b in s:
            bloc_rankings[b].append(rank_points)
            
    return bloc_rankings

def bloc_type_to_avg_rank(bloc_type_ballot):
    """
    Given a bloc type ballot, convert to avg rank encoding. eg A>B>A becomes (2 2 | 2)

    Arguments:
        bloc_type_ballot (list[str]): list of strings represent bloc type ballot. eg ["AA", "B"]
            (with all remaining candidates tied at bottom)

    Returns:
        dict[str, list]: (bloc, avg_rank_vector) dictionary
    """
    bloc_rankings = bloc_ballot_to_rank_encoding(bloc_type_ballot)
    return {b: [np.average(vector)]*len(vector) for b, vector in bloc_rankings.items()}

def dist_to_solid_bloc_ballot(bloc_type_ballot, bloc_order):
    """
    Given a bloc type ballot (with all remaining candidates tied at bottom), measure
    swap distance to solid bloc ballot via rank L_1 method. Rounds distance to 4 decimals.

    Arguments:
        bloc_type_ballot (list[str]): list of strings represent bloc type ballot. eg ["AA", "B"].
            (with all remaining candidates tied at bottom)
        bloc_order (str): the order of blocs to consider solid. eg "AB"

    Return:
        float: distance to solid bloc ballot. Rounds distance to 4 decimals.
    """
    bloc_counts = {b:len([bloc for s in bloc_type_ballot for bloc in s if bloc == b])
                                                 for b in bloc_order}

    # first convert bloc_type_ballot to averaged rank encoding
    avg_rank_ballot = bloc_type_to_avg_rank(bloc_type_ballot)

    # then compute the solid bloc ballot
    solid_bloc_ballot = "".join([b*bloc_counts[b] for b in bloc_order])
    
    # convert it to averaged rank encoding
    avg_rank_solid = bloc_type_to_avg_rank(solid_bloc_ballot)

    # compute L_1 distance between the two
    l_1 =  sum(sum(abs(x-y) for x,y in zip(avg_rank_ballot[b], avg_rank_solid[b])) for b in bloc_order)

    return round(l_1/2, 4)

def name_ballot_to_bloc_type(ballot: Ballot, cand_to_bloc: dict):
    """
    Convert a single name Ballot object into a bloc type ballot.

    Arguments:
        ballot (votekit.Ballot)
        cand_to_bloc (dict): a dictionary with keys = candidates and values = bloc assignment.
        
    Returns:
        list[str]: a list where each entry is a str denoting the bloc types (with multiplicity)
            at position i. The strings are alphabetized to ensure "AAB" is the same as "ABA".
    
    """
    candidates = list(cand_to_bloc.keys())
    if len(candidates) != len(set(candidates)):
        raise ValueError("Candidate names must be unique.")
    ballot_type = [-1] * len(ballot.ranking)

    for j, s in enumerate(ballot.ranking):
        bloc_str = ""
        for c in s:
            bloc_str += cand_to_bloc[c]
            # candidate names are unique so this always finds the correct one
            try:
                candidates.remove(c)
            except:
                raise ValueError(f"Candidate {c} appeared on ballot multiple times.")
        
        # sort is necessary to ensure that AB is the same as BA
        ballot_type[j] = "".join(sorted(bloc_str))
    
    # put all candidates remaining tied at bottom
    if len(candidates) > 0:
        tied_bloc_str = "".join([cand_to_bloc[c] for c in candidates])
        ballot_type.append("".join(sorted(tied_bloc_str)))
    
    return ballot_type

def profile_to_bloc_ballot_type(profile: PreferenceProfile, cand_to_bloc: dict):
    """
    Convert profile with name ballots to bloc ballots.

    Arguments:
        profile (votekit.PreferenceProfile)
        cand_to_bloc (dict): a dictionary with keys = candidates and values = bloc assignment.
        
    Returns:
        dict: a dict where each key is a ballot type and each value is the weight of that type.
            A ballot type will be a tuple of Counter objects, which describe the number of candidates and blocs
            tied in that position.
    
    """
    ballot_types = {}

    for ballot in profile.ballots:
        # must be hashable for dictionary
        ballot_type = tuple(name_ballot_to_bloc_type(ballot, cand_to_bloc))
        
        if ballot_type in ballot_types:
            ballot_types[ballot_type] += ballot.weight
        else:
            ballot_types[ballot_type] = ballot.weight
        
        
    return(ballot_types)

def dist_profile_to_solid(profile, cand_to_bloc, bloc_order):
    """
    Compute the distance of each ballot in profile to solid bloc ballot under swap distance.
    Assumes each ballot has integer weight.

    Arguments:
        profile (votekit.PreferenceProfile): each ballot must have integer weight
        cand_to_bloc (dict[str, str]): candidate name to bloc dictionary
        bloc_order (str): order of blocs to consider solid. eg "AB"
    """
    # returns a dictionary type:count
    ballot_types = profile_to_bloc_ballot_type(profile, cand_to_bloc)

    if any(ballot.weight != int(ballot.weight) for ballot in profile.ballots):
        raise ValueError("All ballots must have integer weight")
    
    data = [-1]*int(profile.total_ballot_wt)
    k=0
    for ballot_type, weight in ballot_types.items():
        weight = int(weight)
        dist = dist_to_solid_bloc_ballot(ballot_type, bloc_order)
        data[k:k+weight] = [dist]*weight
        k += weight

    return data
    


# l1 trick does not hold for arbitrary ballots
# def swap_dist(bloc_type_ballot_1, bloc_type_ballot_2, blocs):
#     """
#     Given two bloc type ballot (with all remaining candidates tied at bottom), measure
#     swap distance via rank L_1 method. Rounds distance to 4 decimals.

#     Arguments:
#         bloc_type_ballot_1 (list[str]): list of strings represent bloc type ballot. eg ["AA", "B"].
#             (with all remaining candidates tied at bottom)
#         bloc_type_ballot_2 (list[str]): list of strings represent bloc type ballot. eg ["AA", "B"].
#             (with all remaining candidates tied at bottom)
#         blocs (list[str]): list of bloc names

#     Return:
#         float: distance to solid bloc ballot. Rounds distance to 4 decimals.
#     """

#     # first convert bloc_type_ballot to averaged rank encoding
#     avg_rank_ballot_1 = bloc_type_to_avg_rank(bloc_type_ballot_1)
#     avg_rank_ballot_2 = bloc_type_to_avg_rank(bloc_type_ballot_2)

#     print(avg_rank_ballot_1,avg_rank_ballot_2)

#     # compute L_1 distance between the two
#     l_1 =  sum(sum(abs(x-y) for x,y in zip(avg_rank_ballot_1[b], avg_rank_ballot_2[b])) for b in blocs)

#     return round(l_1/2, 4)



def diss_to_solid(slate_ballot, slate_to_cand_num, bloc_order):
    """
    Compute the dissimilarity between a ballot and solid.
    For incomplete ballots, this is the minimum swap distance between the completion point cloud
    of the ballot and solid. Does NOT handle ballots with arbitrary ties.
    Slate ballot can be entered with or without the missing slates at the end as a tie.


    Args:
        slate_ballot (list[str]): ["A", "A", "B"]
        slate_to_cand_num (dict[str, int]): {"A":3, "B":2}
        bloc_order (str): the order of blocs to consider solid. eg "AB"

    """
    for i,s in enumerate(slate_ballot):
        if len(s) > 1 and i != len(slate_ballot)-1:
            raise TypeError("Ballot has arbitrary tie")

    # handles ignoring arbitrary ties at the end
    sigma = [s for s in slate_ballot if len(s) == 1]
    sigma_record = sigma.copy()
    sigma_completion = sigma.copy()

    solid_bloc_ballot = [bloc_order[0] for _ in range(slate_to_cand_num[bloc_order[0]])]+[bloc_order[1] for _ in range(slate_to_cand_num[bloc_order[1]])]


    for candidate in solid_bloc_ballot:
        if candidate not in sigma_record:
            sigma_completion.append(candidate)
        else:
            sigma_record.remove(candidate)

    return dist_to_solid_bloc_ballot(sigma_completion, bloc_order)


def diss_profile_to_solid(profile, cand_to_bloc, slate_to_cand_num, bloc_order):
    """
    Compute the dissimilarity of each ballot in profile to solid bloc ballot.
    Assumes each ballot has integer weight.

    Arguments:
        profile (votekit.PreferenceProfile): each ballot must have integer weight
        cand_to_bloc (dict[str, str]): candidate name to bloc dictionary
        bloc_order (str): order of blocs to consider solid. eg "AB"
    """
    # returns a dictionary type:count
    ballot_types = profile_to_bloc_ballot_type(profile, cand_to_bloc)

    if any(ballot.weight != int(ballot.weight) for ballot in profile.ballots):
        raise ValueError("All ballots must have integer weight")
    
    data = [-1]*int(profile.total_ballot_wt)
    k=0
    for ballot_type, weight in ballot_types.items():
        weight = int(weight)
        diss = diss_to_solid(list(ballot_type), slate_to_cand_num, bloc_order)
        data[k:k+weight] = [diss]*weight
        k += weight

    return data