from scipy.optimize import fsolve
from functools import partial

def cyclotomic(x,y,n):
    """
    Return the term x^{n-1}+x^{n-2}y+...+xy^{n-2}+y^{n-1}
    from factoring x^n-y^n.

    Arguments:
        x,y (float)
        n (int)

    Returns:
        float
    """

    return sum([(x**(n-i))*(y**(i-1)) for i in range(1, n+1)])



def slate_BT_coh_to_fpv(num_bloc_cands, num_opp_bloc_cands, bloc_coh):
    """
    Computes the expected FPV share of a bloc of voters from cohesion parameter for s-BT.

    Arguments:
        num_bloc_cands (int): number of candidates in current bloc.
        num_opp_bloc_cands (int): number of candidates in opposing bloc.
        bloc_coh (float): the cohesion parameter of the bloc. Must be in [0,1].

    Returns:
        float: FPV share for bloc.

    """

    r,s,p = num_bloc_cands, num_opp_bloc_cands, bloc_coh

    if 0 <= p <= 1:
        return (p**s*cyclotomic(1-p, p, r))/(cyclotomic(1-p, p, r+s))
    else:
        raise ValueError("Cohesion must be in [0,1].")


def slate_BT_fpv_to_coh(num_bloc_cands, num_opp_bloc_cands, fpv):
    """
    Computes the cohesion parameter that would cause slate-BT to have the given fpv share.
    
    Arguments:
        num_bloc_cands (int): number of candidates in current bloc.
        num_opp_bloc_cands (int): number of candidates in opposing bloc.
        fpv (float): the fpv share of the bloc.

    Returns:
        float: cohesion parameter for bloc.
    """

    r,s = num_bloc_cands, num_opp_bloc_cands

    # odd ordering is required to make r,s,fpv keyword arguments for partial call below
    def equation(coh, r=1, s=1, fpv = 1/2):
        return slate_BT_coh_to_fpv(r,s,coh) - fpv
    
    # fsolve takes an equation in one variable and an estimate of where to start, 
    # which we take to be fpv
    coh_list = fsolve(partial(equation, r=r, s=s, fpv=fpv), fpv)

    # equation is proven to be increasing on [0,1] so there is unique solution
    return coh_list[0]




# testing

# r=6
# s=6
# for p in [1/4, 3/4]:
#     print(f"r={r}, s={s}, p={p}, computed fpv= {slate_BT_coh_to_fpv(r,s, p)}")

# print()

# for p in [1/7, 6/7]:
#     print(f"r={r}, s={s}, p={p}, computed fpv= {slate_BT_coh_to_fpv(r,s, p)}")

# print()
# for fpv in [1/7, 1/13, 1/3]:
#     print(f"r={r}, s={s}, fpv={fpv}, computed coh= {slate_BT_fpv_to_coh(r,s,fpv)}")
