import pandas as pd
from pandas.plotting import autocorrelation_plot
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import math
from time import time
import seaborn as sns
import copy


def drift(array):
    log = np.log(array.tail(252)).diff()
    mu =  np.mean(log)
    v = log.var()
    d = mu - (.5*v)
    return d.values*252


def correlation_matrix(array):
    return np.array(np.log(array.tail(252)).diff().corr())


def std(array):
    std = np.log(array.tail(252)).diff().std()*np.sqrt(252)
    return std.values


def joint_dist(dtf):
    sns.set()
    assets = dtf.columns
    cmp = []
    for _ in assets:
        for o in [x for x in assets if x!=_]:
            if (str(_+o) not in cmp) & (str(o+_) not in cmp):
                u = sns.jointplot(x=_,y=o,data= np.log(dtf).diff(),kind="kde")
                cmp.append(str(_+o))
            else:
                pass


def cholesky_simulation(assets,s1,r,sig,
                        correlation_matrix,T,steps):
    dt = T/steps
    cholesky = np.linalg.cholesky(correlation_matrix)
    z = np.random.randn(len(spot.columns),steps+1)
    x = np.matmul(cholesky,z).T
    S = s1*np.exp(np.cumsum((r - 0.5*sig**2)*dt+sig*math.sqrt(dt)*x, axis = 0)) ; S[0] = s1
    S = pd.DataFrame(S,columns = assets)
    return S


def basket_path(assets,s1,r,sig,
                correlation_matrix,T,trials,steps):
    paths = []
    for simulation in range(trials):
        path = cholesky_simulation(assets,s1,r,sig,correlation_matrix,T,steps)
        paths.append(path.mean(axis=1).tolist())
    basket = np.array(paths)
    return basket


def least_squares_price(simulations,strike_percentage,discount_rate,Call=True):
    strike = simulations[0][0]*strike_percentage
    if Call:
        c_p = 1
    else:
        c_p = -1
    paths = simulations
    n = simulations.shape[1] - 1
    for _ in range(n):
        if _==0:
            m = paths[:,-2:]
        else:
            m = paths[:,-(2+_):-_]
        m[:,-1] = np.maximum((m[:,-1] - strike)*c_p,0)*discount_rate
        m[:,-2] = [x if np.maximum((x - strike)*c_p,0)>0 else 0 for x in m[:,-2]]
        adj = m[(m[:,-2]!=0),:]
        X = adj[:,-2]
        Y = adj[:,-1]
        coeff = np.polyfit(X,Y,2)
        m[:,-2] = [coeff[0]*x**2 + coeff[1]*x + coeff[2] if np.maximum((x - strike)*c_p,0)>0 else 0 for x in m[:,-2]]
    return paths