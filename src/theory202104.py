# Theory based on 2021-04 revisions

import pandas as pd
import networkx as nx
import logging
logger = logging.getLogger()
cliques = nx.algorithms.clique.find_cliques



# Pairs and Sequences

def pair_cardinality(x, y, T):
    '''
    Returns the cardinality if (x,y) is pair in T, otherwise it returns -1
    
    This function is also called strong-cardinality
    '''
    if x==y:
        return -1
    intersection=[a for a in T if a==x or a==y ]
    cardinality=int(len(intersection) / 2)
    return cardinality if [x,y]*cardinality==intersection else -1

def pairs_in_trace(T, cardinality=pair_cardinality):
    '''
    Extract the cardinality of each pair in T
    
    By default cardinality=pair_cardinality , the strong cardinality
    
    Returns a dict[(a,b)] = cardinality(a,b,T)
    '''
    Pairs_in_T = {}

    # The alphabet in T
    Sigma_T = list( set( [x for x in T] ) )
    for i in range( len(Sigma_T) -1 ):
        a = Sigma_T[i]

        Pairs_in_T[ (a,a) ] = cardinality(a, a, T)
        for b in Sigma_T[i+1:]:
            Pairs_in_T[ (a,b) ] = cardinality(a, b, T)
            # asymmetric paired property: if (a,b) is paired in T the (b,a) is not
            if Pairs_in_T[ (a,b) ]>=0:
                Pairs_in_T[ (b,a) ] = -1  
            else: 
                Pairs_in_T[ (b,a) ] = cardinality(b, a, T)
    return Pairs_in_T

def sequence_cardinality(S, T):
    '''
    Returns the cardinality if S=abc...z is a sequence in T, otherwise it returns -1
    '''
    # Force type to list
    if type(S)==type(''):
        S = list(S.strip())
        
    # two or more symbols only
    if len(S) < 2:
        return -1

    # Check all symbols are different
    if len(S) != len(set(S)):
        return -1

    intersection=[a for a in T if a in S ]
    cardinality=int(len(intersection) / len(S)  )
    return cardinality if S*cardinality==intersection else -1

# Pair graphs

def _graph_from_dict(P, weights=False):
    G=nx.DiGraph()
    for (a,b), n in P.items():
        if weights:
            G.add_edge(a, b, weight=n)
        else:
            G.add_edge(a, b)
    return G

def pair_graph(T, cardinality=pair_cardinality):
    if type(T) == type(''):
        return pair_graph(list(T.strip()))
    
    P = pairs_in_trace(T, cardinality=cardinality)
    G = _graph_from_dict(P, weights=True)
    G.pd = pandasPair( P  )
    return G

def non_negative_graph(G):
    P = G.pd[ G.pd['pairs'] >= 0 ].to_dict()['pairs']
    G = _graph_from_dict(P, weights=True)
    G.pd = pandasPair( P  )
    return G

def n_layer(G, n):
    P = G.pd[ G.pd['pairs'] == n ].to_dict()['pairs']
    G = _graph_from_dict(P)
    G.pd = pandasPair( P  )
    return G


# Helpers

def pandasPair(P):
    return  pd.DataFrame.from_dict( 
        { (a[0],a[1]):b for a,b in P.items() }, 
        orient='index', 
        columns=['pairs'] 
    )