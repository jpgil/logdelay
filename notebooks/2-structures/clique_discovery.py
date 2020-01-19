# Clique Discovery

# Minimum frequency of pairs
MIN_CLIQUE_FREQ=0


MIN_CLIQUE_NUMBER=0

# Add START/END nodes to the graph
ADD_START_END=False

# Tolerance when checking parallel executions. Default=0
CLEANSING_TOLERANCE=0


import networkx as nx
import scipy
import matplotlib.pyplot as plt



def created_auxiliary_graph( weighted_paths ):
    
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



def compute_paths_loops(G_bi):
    # Search loops...
    # Transform in single paths
    # And the recover the info at the end, very end

    # Example of components: [{'d', 'c', 'f', 'e'}, {'k', 'j', 'h'}]
    bi_components = nx.connected_components( nx.to_undirected(G_bi) )
    
    # Obtain the loops
    # EXAMPLE: ['c', 'f'], ['k', 'h']
    loops=[]
    for nodes in bi_components:
        # I have to demonstrate this...
        # Extremes has in_degree=out_degree=1
        ex = [ u for u in nodes if G_bi.in_degree(u) * G_bi.out_degree(u) == 1 ]
        if len(ex) != 2:
            raise ValueError("I was wrong.... %s has different degree than expected." % nodes)
        loops.append( list(nx.shortest_simple_paths(G_bi, ex[0], ex[1]))[0] )
    return loops


def loops_graph(G):
    # First generated graph just with bidireccional paths in G:
    G_bi = nx.DiGraph()
    for u in G.nodes():
        for v in G.nodes():
            if (u,v) in G.edges() and (v,u) in G.edges():
                G_bi.add_edge( u, v, weight=max( G.edges[u,v]["weight"], G.edges[v, u]["weight"] ) )
                G_bi.add_edge( v, u, weight=max( G.edges[u,v]["weight"], G.edges[v, u]["weight"] ) )
    return G_bi



def remove_serial_cycles(G, G_bi):
    # Remove the inverse loop and preserve
    # the loop info for the future
    loops_in_right_order = []
    for L in compute_paths_loops(G_bi):
        # The order is given by frequeny!!! Again the blessed frequency...
        a, z = L[0], L[1]
        if G.edges[a,z]['weight'] > G.edges[z,a]['weight']:
            loops_in_right_order.append( L )
        else:
            loops_in_right_order.append( list(reversed(L)) )

    # Now convert G in a tree by removing loop backwards :)
    # And store the edge to be added at the end
    # Example: {('f', 'c'): 1.5, ('k', 'h'): 0.5}

    loopweights = {}
    
    for L in loops_in_right_order:
        loopweights[ (L[-1], L[0]) ] = G.edges[L[1], L[0]]['weight']
        for i in range( len(L)-1, 0, -1 ):
            G.remove_edge(L[i], L[i-1])
    
    return G, loopweights


def cleanse_parallel_artifacts(G, cleansing_tolerance=CLEANSING_TOLERANCE):
    """
    Rationale: A loop doubles the frequency in (A,B) or (B,A)
    Instead, in a parallel exec, f(A,B) / f(B/A) != 2
    
    Prove!! --- -FALSE!!!
    
    Biut, for some strange reason the frequency of serial loops are 
    always integer
    
    Prove!! --- FALSE!!!
    
    But... it seems that numbers are factirs of 0.5
    """
    
    to_remove=[]
    for u in G.nodes():
        for v in G.nodes():
            if (u,v) in G.edges() and (v,u) in G.edges():
                a, b = round( G.edges[u,v]["weight"], 9 ), round( G.edges[v,u]["weight"], 9 )
                w1, w2 = max(a,b), min(a,b)
#                 if abs( w1 - 2*w2 ) > 0 + cleansing_tolerance:
                if a != round(a) and b != round(b):
                    to_remove.append((u, v))   
                    
    print(to_remove)
    for u, v in to_remove:
        if (u,v) in G.edges:
            G.remove_edge(u,v)
        if (v,u) in G.edges:
            G.remove_edge(v,u)

    return G


def minimally_connected_graph( inferred_paths ):

    G = created_auxiliary_graph( inferred_paths )
    
    G = cleanse_parallel_artifacts(G)
    
    G_bi = loops_graph(G)
    G, loopweights = remove_serial_cycles(G, G_bi)
        
        
    # Untangle extra edges from G
    
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
                
    # Now restore the loop and the weight
    
    for e, weight in loopweights.items():
        G_minimal.add_edge( e[0], e[1], weight=weight )
    
    
    return G_minimal

    

def get_successor_pairs( T_prime, addStartEnd=ADD_START_END ):
    """
    Get near successor pairs
    
    Given the trace $T' = s_1 ... s_L$
    For every $1 <= i <= L$ find the maximal subtrace starting at $i$
    $T_i_j = s_i ... s_j$ such that $s_i \ne s_k$ for all $i < k <= j$
    
    Return the concatenation for all $T_i_j$
    [ (s_i, s_k) ] for all s_i \in T_i_j, s_k \in T_i_j for all i < k <= j

    
    >>> get_successor_pairs(list("ABCD"))
    [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D')]
    """
    pairs = []
    for i in range(0, len(T_prime)-1):


        partial_subtrace = T_prime[i:]

        s_i = partial_subtrace.pop(0)
        L = len(partial_subtrace)

        # Find first first j such s_i == s_j, or L if not exists
        if s_i in partial_subtrace:
            j = partial_subtrace.index(s_i)
        else:
            j = L

        # This is the subtrace T_i_j, the maximal that not contains s1
        # (Actually, it not contains s_i)
        T_i_j=partial_subtrace[:j]

        # Construct all s_i, s_k , i < k <= j
        for s_k in T_i_j:
            e = (s_i, s_k)
            pairs.append(e)
            
            # Added 2020-01-18: global star / end
            if ADD_START_END:
                pairs.append( ("_START_", s_i) )
                pairs.append(( s_k, "_END_") )


    return pairs




def get_successor_pairs_by_freq( traces, sensitivity=-1 ):
    """
    Get successor pairs in every T in traces, and combine them by frequency of appearance.
    
    >>> T = [ list("ABC"), list("ABCABC") ]
    >>> get_successor_pairs_by_freq(T)
    {('A', 'B'): 3, ('A', 'C'): 3, ('B', 'C'): 3, ('B', 'A'): 1, ('C', 'A'): 1, ('C', 'B'): 1}
    """
    pairs_by_freq = {}
    L = float(len(traces))

    for trace in traces:
        for pair in get_successor_pairs(trace):
            if pair in pairs_by_freq.keys():
                pairs_by_freq[pair] = pairs_by_freq[pair] + 1.0/L
            else:
                pairs_by_freq[pair] = 1.0/L
            
    return pairs_by_freq




def cluster_same_freq(pairs_dic):
    """
    Group pairs in clusters with same frequency
    
    >>> T = [ list("ABC"), list("ABCABC") ]
    >>> cluster_same_freq( get_successor_pairs_by_freq(T) )
    {3: [('A', 'B'), ('A', 'C'), ('B', 'C')], 1: [('B', 'A'), ('C', 'A'), ('C', 'B')]}
    """    
    freq = list(set(pairs_dic.values()))
    groups = {}
    for pair in pairs_dic.keys():
        f  = pairs_dic[pair]
        if f in groups.keys():
            groups[f].append( pair )
        else:
            groups[f] = [ pair ]
    return groups


# --- Core Step --- #
def infer_paths_from_cliques( pairs ):
    """
    >>> infer_paths_from_cliques( get_successor_pairs(list("ABCA")) )
    []
    >>> infer_paths_from_cliques( get_successor_pairs(list("ABCD")) )
    [['A', 'B', 'C', 'D']]
    >>> infer_paths_from_cliques( [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D')] )
    [['A', 'B', 'C', 'D']]
    >>> infer_paths_from_cliques( get_successor_pairs(list("ABCD")) )
    [['A', 'B', 'C', 'D']]
    """
    paths = []

    G = nx.DiGraph()
    G.add_edges_from( pairs )

    # Search cliques
    G_prime=nx.to_undirected(G) 
    for V in nx.algorithms.clique.find_cliques(G_prime):

        # Create complete graph from clique
        G_complete = G.copy()
        for node in set(G_complete.nodes).difference( set(V) ):
            G_complete.remove_node(node)

            
        # Order nodes by inner degree
        nodes = sorted( G_complete.in_degree() , key=lambda p: p[1], reverse=False)
                
        # Strict checking: in_degree(n) in [0, ... , len(N)-1]
        if all( [in_degree == i for i, (a, in_degree) in zip(range(0, len(nodes)), nodes)]):
            paths.append ( [ a for a,b in nodes ] )

        
    return paths




def infer_paths_from_traces( traces, reduce=False, minsymbols=0):
    """
    >>> infer_paths_from_traces( [list("ABAB")] )
    {2: [['A', 'B']], 1: [['B', 'A']]}
    """
    cluster = cluster_same_freq( get_successor_pairs_by_freq(traces) )
    paths = {}
    path_f = []
    for f in sorted(cluster.keys(), reverse=True):

        successor_pairs  = cluster[f]

        path_f = []
        for X in infer_paths_from_cliques( successor_pairs ):
            if len(X) >= minsymbols:
                path_f.append(X)

        if len(path_f) > 0:
            paths[f] = path_f
                
    """
    Now... I should search for disjoint paths U={ S_i in Gpaths / S_i intersect S_j == {} }
    """
    return paths
    
    

    
if __name__ == "__main__":
    import doctest
    doctest.testmod()