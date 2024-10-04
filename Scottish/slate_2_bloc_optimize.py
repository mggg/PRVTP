from swap_distance import dist_profile_to_solid
import sys
from optimize_helper import peter_estimate_2_bloc_parameters, generate_solid_profile
from votekit.cvr_loaders import load_scottish
import numpy as np
from votekit import PreferenceInterval, Ballot
from scipy.stats import wasserstein_distance, kstest
import votekit.ballot_generator as bg
from votekit import PreferenceProfile
import pickle
from slate_emd import slate_earth_mover_dist
from tqdm import tqdm
import itertools


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
    if model_str not in ["n-BT", "n-PL", "solid"]:
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
    elif model_str != "solid":
        candidates = []
        for c_list in slate_to_candidates.values():
            candidates += c_list

        aa_interval = {
            f"A_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["A"]["A"].values())
        }
        ab_interval = {
            f"B_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["A"]["B"].values())
        }

        ba_interval = {
            f"A_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["B"]["A"].values())
        }
        bb_interval = {
            f"B_{i}": p
            for i, p in enumerate(model_parameters["pref_intervals"]["B"]["B"].values())
        }

        pref_intervals_by_bloc = {
            "A": {
                "A": PreferenceInterval(aa_interval),
                "B": PreferenceInterval(ab_interval),
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

    elif model_str == "solid":
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


def find_min_pi_ab(
    model_str,
    models,
    model_parameters,
    slate_scottish_profile,
    slate_to_candidates,
    cand_list,
    bloc_voter_prop,
    bloc_to_cand_num,
    cand_to_party,
    b_bloc_parties,
    pi_coarse,
    MCMC_sample_size: int = 10000,
):

    n_b_cands = sum(cand_to_party[c] in b_bloc_parties for c in cand_list)
    n_a_cands = len(cand_list) - n_b_cands

    slate_dict = {
        "A": [f"A_{i}" for i in range(n_a_cands)],
        "B": [f"B_{i}" for i in range(n_b_cands)],
    }

    scales = [0.1, 0.01, 0.001]

    lower_b = 0.01
    upper_b = 0.99

    lower_a = 0.01
    upper_a = 0.99

    progress_bar = tqdm(total=len(scales) * pi_coarse**2)

    if model_str in ["IC", "IAC"]:
        return "N/A", "N/A"

    for scale in scales:
        wass_distances = []
        pi_vector = []
        for pi_b in np.linspace(lower_b, upper_b, pi_coarse):
            for pi_a in np.linspace(lower_a, upper_a, pi_coarse):
                pi_vector.append((pi_a, pi_b))

                cohesion_parameters = {
                    "A": {"A": pi_a, "B": 1 - pi_a},
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

                if sum(bloc_to_cand_num.values()) >= 12 and model_str in [
                    "n-BT",
                    "s-BT",
                ]:
                    if model_str == "n-BT":
                        profile = bg.generate_profile_MCMC(MCMC_sample_size)
                    else:
                        profile = bg.generate_profile(
                            MCMC_sample_size, deterministic=False
                        )

                elif model_str == "solid":
                    solid_profile_b = generate_solid_profile(
                        pi_b,
                        int(
                            bloc_voter_prop["B"] * slate_scottish_profile.num_ballots()
                        ),
                        bloc_to_cand_num,
                    )
                    solid_profile_a = generate_solid_profile(
                        pi_a,
                        int(
                            bloc_voter_prop["A"] * slate_scottish_profile.num_ballots()
                        ),
                        bloc_to_cand_num,
                    )
                    profile = solid_profile_a + solid_profile_b
                else:
                    try:
                        profile = bg.generate_profile(
                            int(slate_scottish_profile.num_ballots())
                        )
                    except Exception as e:
                        print(
                            f"Tried to generate profile for {model_str} with {pi_a} {pi_b} and "
                        )

                # wd = wasserstein_distance(scot_data, distances)
                wass_distances.append(
                    slate_earth_mover_dist(slate_scottish_profile, profile, slate_dict)
                )
                progress_bar.update(1)

        min_w = min(wass_distances)
        min_pi_a, min_pi_b = pi_vector[wass_distances.index(min_w)]

        lower_b = max(min_pi_b - scale * 0.5, 0.01)
        upper_b = min(min_pi_b + scale * 0.5, 0.99)

        lower_a = max(min_pi_a - scale * 0.5, 0.01)
        upper_a = min(min_pi_a + scale * 0.5, 0.99)

    return min_pi_a, min_pi_b


def find_min_pi_ab_alpha(
    model_str,
    models,
    model_parameters,
    slate_scottish_profile,
    slate_to_candidates,
    cand_list,
    bloc_voter_prop,
    bloc_to_cand_num,
    cand_to_party,
    b_bloc_parties,
    pi_coarse,
    MCMC_sample_size: int = 10000,
):

    n_b_cands = sum(cand_to_party[c] in b_bloc_parties for c in cand_list)
    n_a_cands = len(cand_list) - n_b_cands

    slate_dict = {
        "A": [f"A_{i}" for i in range(n_a_cands)],
        "B": [f"B_{i}" for i in range(n_b_cands)],
    }

    scales = [0.1, 0.01, 0.001]

    lower_b = 0.01
    upper_b = 0.99

    lower_a = 0.01
    upper_a = 0.99

    pi_vals = [0.55, 0.65, 0.75, 0.85, 0.95]
    pi_to_try = list(itertools.product(pi_vals, repeat=2))
    alpha_vals = [0.5, 1, 2]
    alpha_to_try = list(itertools.product(alpha_vals, repeat=4))

    # progress_bar = tqdm(total=len(pi_vals) ** 2 * len(alpha_vals) ** 4)
    progress_bar = tqdm(total=len(pi_to_try) * len(alpha_to_try))

    min_dist = float("inf")
    best_model_settings = None

    for pi_a, pi_b in pi_to_try:
        for aa, ab, ba, bb in alpha_to_try:
            cohesion_parameters = {
                "A": {"A": pi_a, "B": 1 - pi_a},
                "B": {"B": pi_b, "A": 1 - pi_b},
            }

            alphas = {"A": {"A": aa, "B": ab}, "B": {"B": bb, "A": ba}}

            a_cands = list(model_parameters["pref_intervals"]["A"]["A"].keys())
            b_cands = list(model_parameters["pref_intervals"]["B"]["B"].keys())

            new_params = {x: {y: {} for y in ["A", "B"]} for x in ["A", "B"]}

            new_params["A"]["A"] = dict(
                PreferenceInterval.from_dirichlet(a_cands, aa).interval
            )
            new_params["A"]["B"] = dict(
                PreferenceInterval.from_dirichlet(b_cands, ab).interval
            )
            new_params["B"]["A"] = dict(
                PreferenceInterval.from_dirichlet(a_cands, ba).interval
            )
            new_params["B"]["B"] = dict(
                PreferenceInterval.from_dirichlet(b_cands, bb).interval
            )

            model_parameters["pref_intervals"] = new_params

            bg = make_bg_for_model(
                model_str=model_str,
                models=models,
                model_parameters=model_parameters,
                slate_to_candidates=slate_to_candidates,
                bloc_voter_prop=bloc_voter_prop,
                cohesion_parameters=cohesion_parameters,
                alphas=alphas,
            )

            if sum(bloc_to_cand_num.values()) >= 12 and model_str in [
                "n-BT",
                "s-BT",
            ]:
                if model_str == "n-BT":
                    profile = bg.generate_profile_MCMC(MCMC_sample_size)
                else:
                    profile = bg.generate_profile(MCMC_sample_size, deterministic=False)

            elif model_str == "solid":
                solid_profile_b = generate_solid_profile(
                    pi_b,
                    int(bloc_voter_prop["B"] * slate_scottish_profile.num_ballots()),
                    bloc_to_cand_num,
                )
                solid_profile_a = generate_solid_profile(
                    pi_a,
                    int(bloc_voter_prop["A"] * slate_scottish_profile.num_ballots()),
                    bloc_to_cand_num,
                )
                profile = solid_profile_a + solid_profile_b
            else:
                try:
                    profile = bg.generate_profile(
                        int(slate_scottish_profile.num_ballots())
                    )
                except Exception as e:
                    print(
                        f"Tried to generate profile for {model_str} with {pi_a} {pi_b} and "
                    )

            # wd = wasserstein_distance(scot_data, distances)
            new_dist = slate_earth_mover_dist(
                slate_scottish_profile, profile, slate_dict
            )

            if new_dist < min_dist:
                min_dist = new_dist
                best_model_settings = (pi_a, pi_b, aa, ab, ba, bb)

            progress_bar.update(1)

    return best_model_settings


if __name__ == "__main__":
    args = sys.argv[1:]
    print("args", args)
    election = str(args[0])
    model = str(args[1])
    bloc_order = str(args[2])

    # dist_profile_to_solid (profile, cand_to_bloc, bloc_order)

    MCMC_sample_size = 10000
    pi_coarse = 50
    pi_coarse = 10

    # b_bloc_parties = ["SLP", "SG", "SLD", "TUSC", "GF"]
    # file_names = {
    #     "fife 2022 21": "../election_data/fife_2022_ward21.csv",
    #     "aberdeen 2017 12": "../election_data/aberdeen_2017_ward12.csv",
    #     "aberdeen 2022 12": "../election_data/aberdeen_2022_ward12.csv",
    #     "angus 2012 8": "../election_data/angus_2012_ward8.csv",
    #     "falkirk 2017 6": "../election_data/falkirk_2017_ward6.csv",
    #     "clackmannanshire 2012 2": "../election_data/clackmannanshire_2012_ward2.csv",
    #     "renfrewshire 2017 1": "../election_data/renfrewshire_2017_ward1.csv",
    #     "glasgow 2012 16": "../election_data/glasgow_2012_ward16.csv",
    #     "north-ayrshire 2022 1": "../election_data/north_ayrshire_2022_north_coast.csv",
    # }

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

    # file_names = {("aberdeen", 2017, 11): "../election_data/aberdeen_2017_ward11.csv"}

    models = {
        "n-BT": bg.name_BradleyTerry,
        "n-PL": bg.name_PlackettLuce,
        "s-BT": bg.slate_BradleyTerry,
        "s-PL": bg.slate_PlackettLuce,
        "CS-C": bg.CambridgeSampler,
        "CS-W": bg.CambridgeSampler,
        "solid": 0,
    }

    # estimate model parameters
    model_parameters = peter_estimate_2_bloc_parameters(
        file_names[election], b_bloc_party_dict[election]
    )

    # optimize!
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

    # try a one bloc model, where cohesion is percentage of first place votes
    slate_to_candidates = {
        b: [f"{b}_{i}" for i in range(bloc_to_cand_num[b])]
        for b in bloc_to_cand_num.keys()
    }
    cand_to_bloc = {c: b for b, c_list in slate_to_candidates.items() for c in c_list}

    bloc_voter_prop = {
        "A": model_parameters["bloc_first"]["A"],
        "B": model_parameters["bloc_first"]["B"],
    }

    min_pi_a, min_pi_b = find_min_pi_ab(
        model_str=model,
        models=models,
        model_parameters=model_parameters,
        slate_scottish_profile=slate_scottish_profile,
        slate_to_candidates=slate_to_candidates,
        cand_list=cand_list,
        bloc_voter_prop=bloc_voter_prop,
        bloc_to_cand_num=bloc_to_cand_num,
        cand_to_party=cand_to_party,
        b_bloc_parties=b_bloc_party_dict[election],
        pi_coarse=pi_coarse,
        MCMC_sample_size=MCMC_sample_size,
    )

    with open(
        f"distance_data/2_bloc/emd_to_scottish_{ward_label}_two_bloc_optimized_{model}_bloc_order_{bloc_order}.pkl",
        "wb",
    ) as f:
        pickle.dump((min_pi_a, min_pi_b), f)

    # min_pi_a, min_pi_b, aa, ab, ba, bb = find_min_pi_ab_alpha(
    #     model_str=model,
    #     models=models,
    #     model_parameters=model_parameters,
    #     slate_scottish_profile=slate_scottish_profile,
    #     slate_to_candidates=slate_to_candidates,
    #     cand_list=cand_list,
    #     bloc_voter_prop=bloc_voter_prop,
    #     bloc_to_cand_num=bloc_to_cand_num,
    #     cand_to_party=cand_to_party,
    #     b_bloc_parties=b_bloc_party_dict[election],
    #     pi_coarse=pi_coarse,
    #     MCMC_sample_size=MCMC_sample_size,
    # )
    # # once compute optimal pi_b, save that pi_b and the corresponding distances to solid

    # with open(
    #     f"distance_data/2_bloc/emd_to_scottish_{ward_label}_two_bloc_optimized_{model}_bloc_order_{bloc_order}_pi_and_alpha.pkl",
    #     "wb",
    # ) as f:
    #     pickle.dump((min_pi_a, min_pi_b, aa, ab, ba, bb), f)
