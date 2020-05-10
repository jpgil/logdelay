# Functions
import networkx as nx

import logging
logger = logging.getLogger()


cliques = nx.algorithms.clique.find_cliques

def successor_graph(T):
    if type(T) == type("a"):
        return successor_graph(list(T))
    
    partial_subtrace = T[:]
    G=nx.DiGraph()
    while len(partial_subtrace):
        s_i = partial_subtrace.pop(0)
        for s_j in [ s_i ] + partial_subtrace:
            if s_i in G and s_j in G[s_i]:
                G[s_i][s_j]['weight'] += 1
            else:
                G.add_edge(s_i, s_j, weight=1)
    return G


def add_graphs(*argv):
    J=nx.DiGraph()
    for u, v in argv[0].edges:
        J.add_edge(u, v, weight=argv[0][u][v]["weight"] )

    for H in argv[1:]:
        for u, v in H.edges:
            if u in J and v in J[u]:
                J[u][v]["weight"] += H[u][v]["weight"]
            else:
                J.add_edge(u, v, weight=H[u][v]["weight"] )
    return J
        
    
    
    
def f_layer(f, G):
    H = nx.DiGraph()
    for u, v in G.edges:
        if G[u][v]["weight"] == f:
            H.add_edge(u, v, weight=G[u][v]["weight"])
    return H





def path_condition( G ):

    # 1) InDeg (a_i) = i+1  (starting at 0)

    # Order nodes by inner degree should be 1,2,3,...
    nodes = sorted( G.in_degree() , key=lambda u: u[1], reverse=False)
    naturals = range(1, len(nodes)+1)

    if not all( [in_degree == i for i, (u, in_degree) in zip( naturals , nodes)] ) :
        logger.debug("Condition '1) InDegree' not met. %s not a path." % list(G.nodes))
        return False
    
    # 2) Weights must be a constant
    
    E    = list(G.edges())
    u, v = E[0]
    constant_weight = G[u][v]["weight"]

    if not all([ G[u][v]["weight"] == constant_weight for u, v in E ] ):
        logger.debug("Condition '2) Weights must be a constant' not met. %s not a path." % list(G.nodes))
        return False
    
    # Conditions are met. It is a path, congratulations mom!
    return True




def clique_graphs( G ):
    CliqueSet = list( nx.algorithms.clique.find_cliques( G.to_undirected() ) )
    
    cGraphs = []
    for CliqueVertices in CliqueSet:
        G_clique = G.copy()

        # remove the nodes not in this clique 
        for node in set(G_clique.nodes).difference( set(CliqueVertices) ):
            G_clique.remove_node(node)   
            
        cGraphs.append(G_clique)
        
    return cGraphs
    
    
    
    
    
from math import sqrt

def loop_condition(G):
    weights = set( [G[u][v]["weight"] for u, v in G.edges() ] )
    
    # There is a f-layer with same nodes than G that verifies path condition
    f = 0
    for w in weights:
        U_C = f_layer(w, G)
        if len(U_C.nodes)==len(G.nodes) and path_condition( U_C ) == True:
            f = w
    if f == 0:
        logger.info("NOT A LOOP. No layer is a path, G=%s" % list(G))
        return False, 0, 0
    
    upper_layer = f_layer(f, G)
    set_of_Wm=set()

    
    for (u, v) in upper_layer.edges:
        if (v, u) not in G.edges:
            # All (v, u) must be in G
            
            logger.info("NOT A LOOP. (v,u)  not in %s" % list(G))
            return False, 0, 0
    
        elif u != v: 
            # Union of weights
            set_of_Wm.add( G[v][u]["weight"] )

    # Ensure only one element
    if len(set_of_Wm) != 1:
        logger.info("NOT A LOOP. more than 2 layers in %s" % list(G))
        return False, 0, 0
    
    # Define lower layer weight
    wm = set_of_Wm.pop()
    
    r = sqrt(f + wm)
    if r != int(r):
        logger.info("NOT A LOOP. The r=sqr(%s %s) not integer" % (wm, f) )
        return False, 0, 0
    
    if not f > wm:
        logger.info("NOT A LOOP. %s < %s is False" % (wm, f) )
        return False, 0, 0
    
    return True, wm, f


def paths_from_trace(C):
    paths_found = []

    sgC2 = successor_graph( C+C )
    weights = set( [sgC2[u][v]["weight"] for u, v in sgC2.edges() ] )
    unique_cliques = set([ tuple( sorted(clique) ) for f in weights for clique in cliques( f_layer(f, sgC2).to_undirected() )  ])
#     components = set([ tuple( sorted(clique) ) for f in weights for clique in cliques( f_layer(f, sgC2).to_undirected() )  ])

    for Vq in unique_cliques:
        H = sgC2.copy()
        for node in set(H.nodes).difference( set(Vq) ):
            H.remove_node(node)
        logger.debug( "searching in %s" % H.nodes )
        is_loop, w1, w2 = loop_condition(H)
        if is_loop:
            path = [ u for u, InDeg  in  sorted( H.in_degree() , key=lambda u: u[1], reverse=False)]
            r    = sqrt(w1+w2)/2
            paths_found.append( (r, path) )
            
    return paths_found

def paths_in_components( G ):
    paths_found = []
    
    C=nx.connected_components( G.to_undirected() )
    for Vq in C:
        H = G.copy()
        for node in set(H.nodes).difference( set(Vq) ):
            H.remove_node(node)
        logger.debug( "searching in %s" % H.nodes )
        if path_condition(H):
            path = [ u for u, InDeg  in  sorted( H.in_degree() , key=lambda u: u[1], reverse=False)]
            u = list(H.nodes)[0]
            r = H[u][u]["weight"]
            paths_found.append( (r, path) )
            
    return paths_found

        