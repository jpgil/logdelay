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

def cliques_from_layer(G):
    CliqueSet = list( nx.algorithms.clique.find_cliques( G.to_undirected() ) )
    return CliqueSet

def induced_graph(G, nodes):
    indG = G.copy()

    # remove the nodes not in this clique 
    for node in set(G.nodes).difference( set(nodes) ):
        indG.remove_node(node)       
    return indG
    
def sequences_from_pair_graph(G):
    smallG = non_negative_graph(G)
    seqs = {}

    unique_layers = smallG.pd['pairs'].unique()
    for n in unique_layers:
        logger.debug('Looking for layer={}'.format(n))
        layer_seqs = []

        Glayer =  n_layer(smallG, n)

        cliques = cliques_from_layer( Glayer )
        logger.debug('Cliques for layer {}: {}'.format(n, cliques))
        
        for clique in cliques:
            deg_by_node = sorted( induced_graph(Glayer, clique).in_degree() , key=lambda u: u[1], reverse=False)
            nodes = [ (node,deg) for node,deg in deg_by_node if node in clique ]

            # Verify property of pair graphs
            naturals = range(1, len(nodes)+1)
            if not all( [in_degree == i-1 for i, (_, in_degree) in zip( naturals , nodes)] ) :
                logger.error("Condition '1) InDegree' not met. %s cannot be ordered as a sequence." % clique )
                raise Exception
            else:                
                layer_seqs.append( [ x for x,_ in nodes ] )
        
        if len(layer_seqs):
            seqs[n] = layer_seqs
            
    return seqs
        

# Helpers

def pandasPair(P):
    return  pd.DataFrame.from_dict( 
        { (a[0],a[1]):b for a,b in P.items() }, 
        orient='index', 
        columns=['pairs'] 
    )