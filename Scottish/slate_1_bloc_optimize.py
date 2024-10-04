from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import estimate_1_bloc_parameters, generate_solid_profile
from votekit.cvr_loaders import load_scottish
import numpy as np
from votekit import PreferenceInterval, Ballot
from scipy.stats import wasserstein_distance, kstest
import votekit.ballot_generator as bg
from votekit import PreferenceProfile
import pickle
from slate_emd import slate_earth_mover_dist
from tqdm import tqdm


def make_bg_for_model(
    model_str,
    models,
    model_parameters,
    slate_to_candidates,
    bloc_voter_prop,
    cohesion_parameters,
    alphas,
):
    bg = None
    if model_str not in ["n-BT", "n-PL", "SB"]:
        if "CS" in model_str:
            if model_str == "CS-W":
                bg = models[model_str].from_params(
                    slate_to_candidates,
                    bloc_voter_prop,
                    cohesion_parameters,
                    alphas,
                    W_bloc="B",
                    C_bloc="A",
                )
            else:
                bg = models[model_str].from_params(
                    slate_to_candidates,
                    bloc_voter_prop,
                    cohesion_parameters,
                    alphas,
                    W_bloc="A",
                    C_bloc="B",
                )
        else:
            bg = models[model_str].from_params(
                slate_to_candidates,
                bloc_voter_prop,
                cohesion_parameters,
                alphas,
            )
    elif model_str != "SB":
        candidates = []
        for c_list in slate_to_candidates.values():
            candidates += c_list

        ba_interval = {
            f"A_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["A"].values())
        }
        bb_interval = {
            f"B_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["B"].values())
        }

        # A pref intervals don't matter because only looking at B bloc voters
        pref_intervals_by_bloc = {
            "A": {
                "A": PreferenceInterval(
                    {
                        c: 1 / len(slate_to_candidates["A"])
                        for c in slate_to_candidates["A"]
                    }
                ),
                "B": PreferenceInterval(
                    {
                        c: 1 / len(slate_to_candidates["B"])
                        for c in slate_to_candidates["B"]
                    }
                ),
            },
            "B": {
                "A": PreferenceInterval(ba_interval),
                "B": PreferenceInterval(bb_interval),
            },
        }
        bg = models[model_str](
            candidates=candidates,
            cohesion_parameters=cohesion_parameters,
            bloc_voter_prop=bloc_voter_prop,
            pref_intervals_by_bloc=pref_intervals_by_bloc,
        )

    elif model_str == "SB":
        pass

    else:
        raise ValueError("invalid model string")

    return bg


def anonymize_slates(prefp, cand_list, cand_to_party, b_bloc_parties):
    cand_to_anon = {}

    a_count = 0
    b_count = 0
    for c in cand_list:
        if cand_to_party[c] in b_bloc_parties:
            cand_to_anon[c] = f"B_{b_count}"
            b_count += 1
        else:
            cand_to_anon[c] = f"A_{a_count}"
            a_count += 1

    bal = prefp.ballots[0]
    all_new_ballots = []
    for bal in prefp.ballots:
        for c in bal.ranking:
            if len(c) > 1:
                raise ValueError("Ties must be resolved before anonymizing")
            new_bal = Ballot(
                ranking=[{cand_to_anon[list(c)[0]]} for c in bal.ranking],
                weight=bal.weight,
            )
            all_new_ballots.append(new_bal)

    all_new_ballots
    new_pref_prof = PreferenceProfile(ballots=all_new_ballots)
    return new_pref_prof


def find_min_pi_b(
    model_str,
    models,
    model_parameters,
    slate_scottish_profile,
    slate_to_candidates,
    cand_list,
    cand_to_bloc,
    bloc_voter_prop,
    bloc_to_cand_num,
    cand_to_party,
    b_bloc_parties,
    pi_b_coarse,
    MCMC_sample_size: int = 10000,
):
    min_dist_pair = (float("inf"), float("inf"))
    min_pi_b = float("inf")

    n_b_cands = sum(cand_to_party[c] in b_bloc_parties for c in cand_list)
    n_a_cands = len(cand_list) - n_b_cands

    slate_dict = {
        "A": [f"A_{i}" for i in range(n_a_cands)],
        "B": [f"B_{i}" for i in range(n_b_cands)],
    }

    scales = [0.1, 0.01, 0.001]
    # scales = [0.1]

    if model_str not in ["IC", "IAC"]:
        progress_bar = tqdm(total=pi_b_coarse * len(scales))
        lower = 0.01
        upper = 0.99
        dist_list = []
        for scale in scales:
            for pi_b in np.linspace(lower, upper, pi_b_coarse):
                # A bloc does not matter here
                cohesion_parameters = {
                    "A": {"A": 1, "B": 0},
                    "B": {"B": pi_b, "A": 1 - pi_b},
                }

                # these are arbitrary; if slate model, ballot type not determined by PrefInt
                # if name model, we use estimated PrefInt
                alphas = {"A": {"A": 1, "B": 1}, "B": {"B": 1, "A": 1}}

                bg = make_bg_for_model(
                    model_str=model_str,
                    models=models,
                    model_parameters=model_parameters,
                    slate_to_candidates=slate_to_candidates,
                    bloc_voter_prop=bloc_voter_prop,
                    cohesion_parameters=cohesion_parameters,
                    alphas=alphas,
                )

                # use MCMC sampling if cannot compute PDF
                if sum(bloc_to_cand_num.values()) >= 12 and model_str == "n-BT":
                    profile = bg.generate_profile_MCMC(MCMC_sample_size)
                elif model_str == "SB":
                    profile = generate_solid_profile(
                        pi_b,
                        int(slate_scottish_profile.num_ballots()),
                        bloc_to_cand_num,
                    )
                else:
                    profile = bg.generate_profile(
                        int(slate_scottish_profile.num_ballots())
                    )

                # profile has generated profile
                # Compute emd from profile to scottish profile
                distance = slate_earth_mover_dist(
                    slate_scottish_profile, profile, slate_dict
                )

                dist_list.append((distance, pi_b))

                progress_bar.update(1)

            min_dist_list = min(dist_list)
            min_dist_pair = min(min_dist_pair, min_dist_list)

            min_pi_b = min_dist_pair[1]

            lower = min_pi_b - scale * 0.5
            upper = min_pi_b + scale * 0.5

        min_pi_b = min_dist_pair[1]

    else:
        g = models[model_str](candidates=list(cand_to_bloc.keys()))
        profile = g.generate_profile(int(slate_scottish_profile.num_ballots()))
        min_pi_b = "N/A"

    if min_pi_b == float("inf") or min_pi_b == "N/A":
        return "N/A"
    else:
        return min_pi_b


if __name__ == "__main__":
    args = sys.argv[1:]
    print("args", args)
    election = str(args[0])
    model = str(args[1])
    bloc_order = str(args[2])

    optimize_for = "WD"  # "KS" #WD

    MCMC_sample_size = 10000

    if election in ["glasgow 2012 16", "north-ayrshire 2022 1"] and model == "s-BT":
        print("lowered pi_b coarse for time reasons")
        pi_b_coarse = 10
    else:
        pi_b_coarse = 50

    b_bloc_party_dict = {
        "aberdeen 2017 11": [
            "Labour (Lab)",
            "Scottish National Party (SNP)",
            "Liberal Democrat (LD)",
        ],
        "aberdeen 2022 11": ["Conservative and Unionist Party (Con)", "Labour (Lab)"],
        "aberdeen 2017 10": ["Conservative and Unionist Party (Con)"],
    }

    file_names = {
        "aberdeen 2017 11": "../election_data/aberdeen_2017_ward11.csv",
        "aberdeen 2022 11": "../election_data/aberdeen_2022_ward11.csv",
        "aberdeen 2017 10": "../election_data/aberdeen_2017_ward10.csv",
    }

    models = {
        "n-BT": bg.name_BradleyTerry,
        "n-PL": bg.name_PlackettLuce,
        "s-BT": bg.slate_BradleyTerry,
        "s-PL": bg.slate_PlackettLuce,
        "CS-C": bg.CambridgeSampler,
        "CS-W": bg.CambridgeSampler,
        "SB": 0,
        "IC": bg.ImpartialCulture,
        "IAC": bg.ImpartialAnonymousCulture,
    }

    # estimate model parameters
    model_parameters = estimate_1_bloc_parameters(
        file_names[election], b_bloc_party_dict[election]
    )

    # optimize!
    data_dict = {}
    wass_dict = {}

    city, year, ward = election.split(" ")
    ward_label = f"{city} ward_{ward} {year}"

    scottish_profile, num_seats, cand_list, cand_to_party, ward = load_scottish(
        file_names[election]
    )

    slate_scottish_profile = anonymize_slates(
        scottish_profile,
        cand_list,
        cand_to_party,
        b_bloc_party_dict[election],
    )

    cand_to_bloc = {
        c: "B" if cand_to_party[c] in b_bloc_party_dict[election] else "A"
        for c in cand_list
    }

    # count the number of candidates in each bloc
    bloc_to_cand_num = {
        "A": len([c for c, bloc in cand_to_bloc.items() if bloc == "A"]),
        "B": len([c for c, bloc in cand_to_bloc.items() if bloc == "B"]),
    }

    scot_data = dist_profile_to_solid(scottish_profile, cand_to_bloc, bloc_order)

    data_dict[f"{ward_label} real"] = scot_data

    # try a one bloc model, where cohesion is percentage of first place votes
    slate_to_candidates = {
        b: [f"{b}_{i}" for i in range(bloc_to_cand_num[b])]
        for b in bloc_to_cand_num.keys()
    }
    cand_to_bloc = {c: b for b, c_list in slate_to_candidates.items() for c in c_list}

    # only looking at B bloc
    bloc_voter_prop = {"A": 0, "B": 1}

    min_pi_b = find_min_pi_b(
        model_str=model,
        models=models,
        model_parameters=model_parameters,
        slate_scottish_profile=slate_scottish_profile,
        slate_to_candidates=slate_to_candidates,
        cand_list=cand_list,
        cand_to_bloc=cand_to_bloc,
        bloc_voter_prop=bloc_voter_prop,
        bloc_to_cand_num=bloc_to_cand_num,
        cand_to_party=cand_to_party,
        b_bloc_parties=b_bloc_party_dict[election],
        pi_b_coarse=pi_b_coarse,
        MCMC_sample_size=MCMC_sample_size,
    )

    print("found")
    print(min_pi_b)

    # once compute optimal pi_b, save that pi_b and the corresponding distances to solid
    with open(
        f"distance_data/1_bloc/emd_to_scottish_{ward_label}_one_bloc_optimized_{optimize_for}_{model}_bloc_order_{bloc_order}_b_bloc_parties_{b_bloc_party_dict[election]}.pkl",
        "wb",
    ) as f:
        pickle.dump(min_pi_b, f)

    print("Done!")
