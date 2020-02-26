# Functions for Cliques Discovery

import networkx as nx
import logging
import sys
import math
logger = logging.getLogger()


def get_successor_by_freq( traces ):
    """
    Get successor pairs in every T in traces, and combine them by frequency of appearance.
    
    >>> T = [ list("ABC"), list("ABCABC") ]
    >>> get_successor_pairs_by_freq(T)
    {('A', 'B'): 3, ('A', 'C'): 3, ('B', 'C'): 3, ('B', 'A'): 1, ('C', 'A'): 1, ('C', 'B'): 1}
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    
    pairs_with_freq = {}
    L = float(len(traces))

    for trace in traces:
        for pair in get_successor_pairs(trace):
            if pair in pairs_with_freq.keys():
                pairs_with_freq[pair] = pairs_with_freq[pair] + 1.0/L
            else:
                pairs_with_freq[pair] = 1.0/L
            
    By_freq = {}
    for (u, v), freq in pairs_with_freq.items():
        f = round(freq,3)
        if f in By_freq.keys():
            By_freq[f].append( (u,v) )
        else:
            By_freq[f] =[ (u,v) ]
    return By_freq



def get_successor_pairs( T_prime ):
    """
    Get near successor pairs
    
    Given the trace $T' = s_1 ... s_L$
    For every $1 <= i <= L$ find the maximal subtrace starting at $i$
    $T_i_j = s_i ... s_j$ such that $s_i \ne s_k$ for all $i < k <= j$
    
    Return the concatenation for all $T_i_j$
    [ (s_i, s_k) ] for all s_i \in T_i_j, s_k \in T_i_j for all i < k <= j
    
    ADDED 2020-01-23:
    Que no se repitan!

    
    >>> get_successor_pairs(list("ABCD"))
    [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D')]
    """

    logger = logging.getLogger( sys._getframe().f_code.co_name )
   
    pairs = []
    for i in range(0, len(T_prime)-1):


        partial_subtrace = T_prime[i:]

        s_i = partial_subtrace.pop(0)
        L = len(partial_subtrace)

        # Find first first j such s_i == s_j, or L if not exists
        # if s_i in partial_subtrace:
        #     j = partial_subtrace.index(s_i)
        # else:
        #     j = L

        # This is the subtrace T_i_j, the maximal that not contains s1
        # (Actually, it not contains s_i)
        T_i_j=partial_subtrace[:] # Andres 20200124 .. all friends with all, including loops
        
        T_i_j_pairs = [] # 2020-01-23 BEHAVIOR ... but not remove, it doesn't affect

        # Construct all s_i, s_k , i < k <= j
        for s_k in T_i_j:
            e = (s_i, s_k)

            pairs.append(e)       # 2020-01-20 Old BEHAVIOR
            

    logger.debug("Found pairs: %s" % (pairs) )
    return pairs


def successorsGraph(successor_by_freq):
    G=nx.DiGraph()
    for f, pairs in successor_by_freq.items():
        for u, v in pairs:
            G.add_edge(u, v, weight=f)
    return G





# Sort the cliques and apply the rules:
# 1) The nodes of a single path in their equivalent pair has in_degree=0,1,2,...
# 2) A path is composed for at least 2 ... 3? nodes

def infer_paths(G_freq, min_clique_size=3):
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    logger.debug("Received a dict G with f=%s" % G_freq.keys())

    paths_f = {}
    cliques_f = { f: list(nx.algorithms.clique.find_cliques( G_freq[f].to_undirected() )) for f in G_freq.keys() }
    logger.debug("All cliques are %s" % cliques_f)
        
    for f, cliques in cliques_f.items():
#         logger.debug("Clique[%d] = %s" % (f, cliques) )
        paths = []
        for clique in cliques:
            logger.debug("F=%d, clique=%s" % (f, clique))
    
            # From the original graph(f),
            G_complete = G_freq[f].copy()
            
            # remove the nodes not in this clique 
            for node in set(G_complete.nodes).difference( set(clique) ):
                G_complete.remove_node(node)
                
            # Order nodes by inner degree
            nodes = sorted( G_complete.in_degree() , key=lambda p: p[1], reverse=False)
            logger.debug("Nodes: %s" %  nodes)

            # - core - CRITERIA 1 and 2
            # Strict checking: in_degree(n) in [0, ... , len(N)-1]
            if len(nodes) >=min_clique_size and ( 
                all( [in_degree == i for i, (a, in_degree) in zip(range(0, len(nodes)), nodes)] ) 
                or
                all( [in_degree == i+1 for i, (a, in_degree) in zip(range(0, len(nodes)), nodes)] ) 
            ):
                    paths.append ( [ a for a, in_degree in nodes ] )
            else:
                logger.debug("This clique doesn't match the in_degree critera, or it is too small: %s" % nodes)
        if paths:
            paths_f[f] = paths

    logger.info("Paths inferred (min_clique_size=%d: %s)" % (min_clique_size, paths_f) )
    return paths_f




def split_in_freqGraphs( successorsGraph ):
    
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    u_v_f = [ (u, v, successorsGraph[u][v]["weight"]) for u, v in successorsGraph.edges]
    frqs = set([ f for u, v, f in u_v_f])
    logger.debug("freqs found: %s" % frqs)
    G={}
    for f in frqs:
        G[f] = successorsGraph.copy()
        # Get all nodes whose pairs has weight!=f
        for u, v, f2 in u_v_f:
            if f != f2:
                G[f].remove_edge(u,v)
        logger.debug("Nodes in freq=%d: %s" % (f, G[f].nodes) )
        
    logger.debug("About to return a set of G with f=%s" % G.keys())
    return G






def remove_loops_in_trace(paths_loop, succ_G):
    """
    A loop... should be disjoint with other loops?
    I believe YES
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )

    loops_found = []
    loops_candidates = []


    # Look also backwards (it worked!)
    for f, paths_f in paths_loop.items():
        
        for path in paths_f:
            for p in [ path, list(reversed(path)) ]:
                # Magic here
                is_a_loop, L = find_loops_in_path(p, succ_G)

                if is_a_loop:
                    if (L,p) not in loops_candidates:
                        loops_candidates.append( (L,p) )
                        logger.info("Loop candidate FOUND: repeated %d times in this trace, loop: %s" % (L, p) )
                else:
                    logger.debug("It seems that p is not a loop: %s" % p)
                

    loops_found = loops_candidates

                
    for L, p in loops_found:

        # Write correct frequency L for the loop.
        for i_u in range(0, len(p)-1):
            for i_v in range(i_u + 1, len(p) ):
                u, v = p[i_u], p[i_v]
                logger.debug("(%s, %s) weight updated from %d to %d" % (u,v,succ_G[u][v]['weight'], L) )
                succ_G[u][v]['weight'] = float(L)

        # Then remove the back edges from succ_G
        # I already stated that the loop is A...Z, then I will remove Z...A
        for i_u in range(0, len(p)):
            for i_v in range(i_u, len(p)):
                logger.debug("Removing %s, %s" % (p[i_v], p[i_u]))
                try:
                    succ_G.remove_edge(p[i_v], p[i_u])
                except:
                    logger.debug("Hohoho! that pair was already removed")

        logger.debug("Removed %s" % list(reversed(p)))
    return loops_found, succ_G




def find_loops_in_path(p, succ_G):
    """
    With all pairs, if ABC is a loop in pairs of len L then 
    f(A,B) = f(B,C) = L(L+1)/2 and f(B,A) = f(C,B) = L(L-1)/2
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    is_a_loop, L = False, 0

    # Check if p is a loop
    logger.debug("Check if p is a loop: %s" % p)
    for a, b in [ (a,b) for a,b in zip( p[:-1], p[1:] )  ]:

        is_a_loop = True
        setL = set()
        if is_a_loop and (b, a) in succ_G.edges() and (a, b) in succ_G.edges():
            Wab = succ_G[a][b]['weight'] # also, Wab=f by construction
            Wba = succ_G[b][a]['weight']
            
            # Combinatory test:
            """
            W1 = (L+1)*L/2.0 = (L^2 + L)/2
            W2 = L*(L-1)/2.0 = (L^2 - L)/2
            2*W1 = L^2 + L
            2*W2 = L^2 - L
            2(W1+W2) = 2 L^2
            L = sqr(W1+W2) # Integer
            """
            L = int( math.sqrt(Wab + Wba) )
            Lplus1, Lminus1 = (L+1)*L/2.0, L*(L-1)/2.0
            
            # All lengths L must be equal, therefore the set of L must contains 1 and only 1 element
            setL.add(L)

            logger.debug( (a, b, Wab, Lplus1, Wba, Lminus1, L ))
            
            # Does it agree with combinatory test?
            if Wab != Lplus1 or Wba != Lminus1:
                is_a_loop = False
        else:
            is_a_loop = False     
            
    if is_a_loop and len(setL) != 1:
        is_a_loop = False

    return is_a_loop, L


def remember_loops( loops_this_trace, all_loops ):
    # Add loops found in this pair to the loops in all traces
    for L,p in loops_this_trace:
        pt = tuple(p)
        if pt not in all_loops.keys():
            all_loops[pt] =  float(L)
        else:
            all_loops[pt] += float(L)	
    return all_loops




def unentangled_DAG(succ_DAG):
    succ_G_acyclic_forReal = nx.DiGraph()
    E = succ_DAG.edges()
    for u, v in E:
        if (v, u) not in E:
            succ_G_acyclic_forReal.add_edge(u, v, weight=succ_DAG[u][v]["weight"]  )
        else:
            logger.debug("Removing (%s, %s)" % (u,v))
    return succ_G_acyclic_forReal


def combine_DAGs(succ_G_acyclic_forReal, G):
    if not G:
        G = succ_G_acyclic_forReal.copy()
    else:
        for u,v in succ_G_acyclic_forReal.edges():
            Gw = succ_G_acyclic_forReal[u][v]["weight"]
            if (u,v) not in G.edges():
                G.add_edge(u, v, weight=Gw)
            else:
                G[u][v]["weight"] += Gw
    return G





def path_graph( weighted_paths ):
    
    def append_path(G, path, weight):
        edges = []
        previous = path[0]
        for node in path[1:]:
            edges.append( (previous, node, {"weight": round(weight, 2)} ) )
            previous = node
        G.add_edges_from(edges)

    G = nx.DiGraph()
    for w in sorted(weighted_paths, reverse=True):
        for path_w in weighted_paths[w]:
            append_path( G, path_w, w )            
    return G




#2020-01-25
# If paths (u,z,v) and (u,v) exists, leave just (u,z,v)
def minimally_connected(G):
    G_minimal = G.copy()
    
    for u, v in G.edges():

        # u has already v, then I will work if I have more than one neighbor
        if len(G[u]) > 1:
            remove_edge = False
            # look if I have a longest u,z,v path
            for z, attr in G[u].items():
                if z != v and z != u:
                    if nx.has_path(G_minimal, z, v):
                        remove_edge = True
            if remove_edge:
                G_minimal.remove_edge( u, v )    
    return G_minimal






