# %%
import votekit.ballot_generator as bg
import pickle, sys

arguments = sys.argv[1:]
generator = arguments[0]
pi_type = arguments[1]
n_cands_W = int(arguments[2])
n_cands_C = int(arguments[2])

# print(f"{generator} {pi_type} cohesion .7 W_bloc 2x2 candidates")

with open(f'ranked_marginals_profiles/{generator}_{pi_type}_nW_{n_cands_W}_nC_{n_cands_C}.pkl', 'rb') as file:
    ballot_dict = pickle.load(file)


slate_to_candidates = {"W": [f"W{i}" for i in range(n_cands_W)],
                       "C": [f"C{i}" for i in range(n_cands_C)]}

candidates_to_slates = {c:b for b,c_list in slate_to_candidates.items() for c in c_list}

# convert from candidate names to slate names
ballot_frequencies = {}
for b,f in ballot_dict.items():
    ballot_by_slate  = tuple([candidates_to_slates[c] for c in b])

    if ballot_by_slate in ballot_frequencies.keys():
        ballot_frequencies[ballot_by_slate] += f
    
    else:
        ballot_frequencies[ballot_by_slate] = f

total_votes = sum(ballot_frequencies.values())
print(f"There are {total_votes} many ballots (counted with frequency) in the profile.")


# which bloc comes first
total_w_first = sum([f for b,f in ballot_frequencies.items() if b[0] == "W"])
total_c_first = sum([f for b,f in ballot_frequencies.items() if b[0] == "C"])
print(f"1st place W {total_w_first} {total_w_first/float(total_c_first+total_w_first)*100:.2f} %" )
print(f"1st place C {total_c_first} {total_c_first/float(total_c_first+total_w_first)*100:.2f} %" )

# %%
# 2nd place votes for each bloc
w =sum([f for b,f in ballot_frequencies.items() if len(b)>=2 and b[1] == "W" ])
c = sum([f for b,f in ballot_frequencies.items() if len(b)>=2 and b[1] == "C" ])
t = float(w+c)
print("2nd place W", w, round(w/t*100, 4), "%")
print("2nd place C", c, round(c/t*100, 4), "%")

# %%
# 3rd place votes for each bloc
w = sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[2] == "W" ])
c = sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[2] == "C" ])
t = float(w+c)
print("3rd place W", w, round(w/t*100, 4), "%")
print("3rd place C", c, round(c/t*100, 4), "%")

# %%
# 4th place votes for each bloc
w = sum([f for b,f in ballot_frequencies.items() if len(b)>=4 and b[3] == "W" ])
c = sum([f for b,f in ballot_frequencies.items() if len(b)>=4 and b[3] == "C" ])
t = float(w+c)
print("4th place W",  w, round(w/t*100, 4), "%")
print("4th place C", c, round(c/t*100, 4), "%\n")

# %%
# borda count
ballot_length = len(list(ballot_dict.keys())[0])
print("borda length", ballot_length)
w_borda = sum(
    [sum(
        [1*(ballot_length-i) for i, cand in enumerate(b[:ballot_length]) if cand == "W"])
        *f 
        for b,f in ballot_frequencies.items()]
        )

c_borda = sum(
    [sum(
        [1*(ballot_length-i) for i, cand in enumerate(b[:ballot_length]) if cand == "C"])
        *f 
        for b,f in ballot_frequencies.items()]
        )

total_borda = float(sum(
    [sum(
        [1*(ballot_length-i) for i, cand in enumerate(b[:ballot_length])])
        *f 
        for b,f in ballot_frequencies.items()]
        ))


print(f"W candidates received {w_borda} borda points which is {w_borda/total_borda*100:.2f} percent")
print(f"C candidates received {c_borda} borda points which is {c_borda/total_borda*100:.2f} percent")
print("Total borda", total_borda, "\n")


# %%
# conditioned on first place vote, explore different metrics
ballot_length = len(list(ballot_dict.keys())[0])
for header in ["C", "W"]:
    print("headed by", header)
    borda_c = sum(
        [sum(
        [1*(ballot_length-i) for i, cand in enumerate(b[:ballot_length]) if cand == "C"])
        *f 
        for b,f in ballot_frequencies.items() if b[0] == header]
        )
    borda_w = sum(
        [sum(
        [1*(ballot_length-i) for i, cand in enumerate(b[:ballot_length]) if cand == "W"])
        *f 
        for b,f in ballot_frequencies.items() if b[0] == header]
        )
    
    total_borda = float(borda_c + borda_w)

    print(f"Borda score for C candidates {borda_c} which is {borda_c/total_borda*100:.2f} percent")
    print(f"Borda score for W candidates {borda_w} which is {borda_w/total_borda*100:.2f} percent")

    second_c=sum([f for b,f in ballot_frequencies.items() if b[0] == header and len(b)>=2 and b[1] == "C" ])
    second_w=sum([f for b,f in ballot_frequencies.items() if b[0] == header and len(b)>=2 and b[1] == "W" ])
    total = float(second_c+second_w)

    print(f"Second place for C candidates {second_c} which is {second_c/total*100:.2f} percent")
    print(f"Second place for W candidates {second_w} which is {second_w/total*100:.2f} percent")

    third_c = sum([f for b,f in ballot_frequencies.items() if b[0] == header and len(b)>=3 and  b[2] == "C" ])
    third_w = sum([f for b,f in ballot_frequencies.items() if b[0] == header and len(b)>=3 and  b[2] == "W" ])
    total = float(third_c+third_w)
    print(f"Third place for C candidates {third_c} which is {third_c/total*100:.2f} percent")
    print(f"Third place for W candidates {third_w} which is {third_w/total*100:.2f} percent\n")
        

# %%
# # ballot starts CC who comes third
# print("W third", sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[1] == "C" and b[0] == "C" and b[2] == "W"]))
# print("C third", sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[1] == "C" and b[0] == "C" and b[2] == "C"]))

# %%
# # ballot starts WW who comes third
# print("W third", sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[1] == "W" and b[0] == "W" and b[2] == "W"]))
# print("C third", sum([f for b,f in ballot_frequencies.items() if len(b)>=3 and b[1] == "W" and b[0] == "W" and b[2] == "C"]))

# %%
# # bullet votes
# bullet_vote_total = sum([f for b,f in ballot_frequencies.items() if len(b) == 1])
# print(f"There are {bullet_vote_total} many bullet votes")

# %%
# # nine or less (the number of seats available)
# nine_or_less = sum([f for b,f in ballot_frequencies.items() if len(b) <= 9])
# ten_or_more = sum([f for b,f in ballot_frequencies.items() if len(b) > 9])
# print(f"There are {nine_or_less} ballots with 9 or fewer candidates")
# print(f"There are {ten_or_more} ballots with 10 or more.")

# print("Sanity check:")
# print(f"These partition the space {total_votes} = {nine_or_less+ten_or_more}")

# %%
# # mentions in top 9
# w_in_top_9 = sum(
#     [sum(
#         [1 for cand in b[:9] if cand == "W"])
#         *f 
#         for b,f in ballot_frequencies.items()]
#         )

# c_in_top_9 =sum(
#     [sum(
#         [1 for cand in b[:9] if cand == "C"])
#         *f 
#         for b,f in ballot_frequencies.items()]
#         )

# print(f"There are {w_in_top_9} mentions of W candidates in the top 9 slots of all ballots.")
# print(f"There are {c_in_top_9} mentions of C candidates in the top 9 slots of all ballots.")

# print(f"For a total of {w_in_top_9+c_in_top_9}.")


