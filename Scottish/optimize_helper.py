from votekit.cvr_loaders import load_scottish
from votekit import PreferenceProfile, Ballot

def generate_solid_profile(pi_b, num_ballots, bloc_to_cand_num):
    """
    Generate a profile of solid A over B or B over A ballots with proportion of B over A = pi_b

    Arguments:
        pi_b (float): proportion of ballots to be B over A
        num_ballots (int): number of ballots to generate
        bloc_to_cand_num (dict): bloc, number of candidates

    Returns:
        votekit.PreferenceProfile
    """
    solid_a_ballot = Ballot([{f"A_{i}"} for i in range(bloc_to_cand_num["A"])]+[{f"B_{i}"} for i in range(bloc_to_cand_num["B"])], 
                                    weight=int((1-pi_b)*num_ballots))
    solid_b_ballot = Ballot([{f"B_{i}"} for i in range(bloc_to_cand_num["B"])]+[{f"A_{i}"} for i in range(bloc_to_cand_num["A"])], 
                            weight=int(pi_b*num_ballots))
    
    return PreferenceProfile(ballots= [solid_a_ballot,solid_b_ballot])

def estimate_1_bloc_parameters(file_name, b_bloc_parties):
    """
    Computes Borda and FPV share for A and B bloc using parties defined in b_bloc_parties.
    Estimates PrefIntervals by simply tallying FPV for individual candidates.

    Arguments:
        file_name (str): path for scottish election file
        b_bloc_parties (list[str]): list of parties to be considered b_bloc

    Returns:
        dict: keys "bloc_first", "pref_intervals", "borda_share"
    """
    model_parameters = {}
    blocs= ["A", "B"]

    scottish_profile, num_seats, cand_list, cand_to_party, ward = load_scottish(file_name)
    cand_to_bloc = {c:"B" if cand_to_party[c] in b_bloc_parties 
            else "A" for c in cand_list}


    bloc_to_first_place = {bloc: 0.0 for bloc in blocs}
    bloc_to_borda = {bloc: 0.0 for bloc in blocs}
    pref_intervals = {bloc: {c:0.0 for c,b in cand_to_bloc.items() if b == bloc} for bloc in blocs}
    num_cands = len(cand_to_bloc)
    borda_vector = [num_seats-i for i in range(num_seats)] + [0]*(num_cands-num_seats)

    for ballot in scottish_profile.ballots:
        indices = {bloc: [] for bloc in blocs}
        for i,s in enumerate(ballot.ranking):
            if len(s)>1:
                raise ValueError("we do not handle ties in ballots")
            
            candidate, = s
            indices[cand_to_bloc[candidate]].append(i)
            
        bloc_to_borda["B"] += int(ballot.weight)*sum([s for i,s in enumerate(borda_vector) if i in indices["B"]])
        bloc_to_borda["A"] += int(ballot.weight)*sum([s for i,s in enumerate(borda_vector) if i in indices["A"]])

        s = ballot.ranking[0]
        # nifty way to unpack a frozen set with one element
        candidate, = s
        bloc_to_first_place[cand_to_bloc[candidate]] += ballot.weight

        # tally first place votes for preference interval
        pref_intervals[cand_to_bloc[candidate]][candidate] += ballot.weight
        

    pref_intervals = {b: {c:p/sum(pi.values()) for c,p in pi.items()} for b, pi in pref_intervals.items()}

    # get vote share
    bloc_to_first_place = {b:v/scottish_profile.num_ballots() for b,v in bloc_to_first_place.items()}
    bloc_to_borda = {b: v/sum(bloc_to_borda.values()) for b,v in bloc_to_borda.items()}


    model_parameters["bloc_first"] = bloc_to_first_place
    model_parameters["pref_intervals"] = pref_intervals
    model_parameters["borda_share"] = bloc_to_borda

    return model_parameters

def estimate_2_bloc_parameters(file_name, b_bloc_parties):
    """
    Computes Borda and FPV share for A and B bloc using parties defined in b_bloc_parties.
    Estimates PrefInterval AA by FPV for A, AB by first appearance of B on A ballot.
    Same for BA and BB.

    Arguments:
        file_name (str): path for scottish election file
        b_bloc_parties (list[str]): list of parties to be considered b_bloc

    Returns:
        dict: keys "bloc_first", "pref_intervals", "borda_share"
    """
    model_parameters = {}
    blocs= ["A", "B"]

    scottish_profile, num_seats = load_scottish(file_name)
    cand_to_bloc = {c:"B" if c.replace("'","").split(",")[2].strip(")").strip(" ") in b_bloc_parties 
                    else "A" for c in scottish_profile.candidates}


    bloc_to_first_place = {bloc: 0.0 for bloc in blocs}
    bloc_to_borda = {bloc: 0.0 for bloc in blocs}
    # estimating 4 preference intervals
    pref_intervals = {bloc: {b:{c:0.0 for c, c_bloc in cand_to_bloc.items() if c_bloc == b} for b in blocs} for bloc in blocs}
    num_cands = len(cand_to_bloc)
    borda_vector = [num_seats-i for i in range(num_seats)] + [0]*(num_cands-num_seats)

    for ballot in scottish_profile.ballots:
        indices = {bloc: [] for bloc in blocs}
        for i,s in enumerate(ballot.ranking):
            if len(s)>1:
                raise ValueError("we do not handle ties in ballots")
            
            candidate, = s
            indices[cand_to_bloc[candidate]].append(i)
            
        bloc_to_borda["B"] += int(ballot.weight)*sum([s for i,s in enumerate(borda_vector) if i in indices["B"]])
        bloc_to_borda["A"] += int(ballot.weight)*sum([s for i,s in enumerate(borda_vector) if i in indices["A"]])

        s = ballot.ranking[0]
        # nifty way to unpack a frozen set with one element
        fp_candidate, = s
        bloc_to_first_place[cand_to_bloc[fp_candidate]] += ballot.weight

        # estimate preference interval
        # bloc of first place candidate determines if this is for A_ or B_ preference interval
        pref_intervals[cand_to_bloc[fp_candidate]][cand_to_bloc[fp_candidate]][fp_candidate] += ballot.weight

        # find the first candidate of opposite bloc
        for s in ballot.ranking[1:]:
            candidate, = s
            if cand_to_bloc[candidate] != cand_to_bloc[fp_candidate]:
                pref_intervals[cand_to_bloc[fp_candidate]][cand_to_bloc[candidate]][candidate] += ballot.weight
                break
        
    # normalize preference intervals
    pref_intervals = {b: {bloc: {c: v/sum(pi.values()) for c,v in pi.items()} for bloc, pi in pi_dict.items()} 
                                                            for b, pi_dict in pref_intervals.items()}

    # get vote share
    bloc_to_first_place = {b:v/scottish_profile.num_ballots() for b,v in bloc_to_first_place.items()}
    bloc_to_borda = {b: v/sum(bloc_to_borda.values()) for b,v in bloc_to_borda.items()}


    # this is the bloc_proportion estimate
    model_parameters["bloc_first"] = bloc_to_first_place
    model_parameters["pref_intervals"] = pref_intervals
    model_parameters["borda_share"] = bloc_to_borda

    return model_parameters