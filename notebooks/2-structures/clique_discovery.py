# Clique Discovery

MIN_CLIQUE_FREQ=0
MIN_CLIQUE_NUMBER=0



import networkx as nx



def get_successor_pairs( T_prime ):
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
    return pairs




def get_successor_pairs_by_freq( traces, sensitivity=-1 ):
    """
    Get successor pairs in every T in traces, and combine them by frequency of appearance.
    
    >>> T = [ list("ABC"), list("ABCABC") ]
    >>> get_successor_pairs_by_freq(T)
    {('A', 'B'): 3, ('A', 'C'): 3, ('B', 'C'): 3, ('B', 'A'): 1, ('C', 'A'): 1, ('C', 'B'): 1}
    """
    pairs_by_freq = {}

    for trace in traces:
        for pair in get_successor_pairs(trace):
            if pair in pairs_by_freq.keys():
                pairs_by_freq[pair] = pairs_by_freq[pair] + 1
            else:
                pairs_by_freq[pair] = 1
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

        # Order nodes by outer degree
        nodes = sorted( G_complete.out_degree() , key=lambda p: p[1], reverse=True)
                
        # Strict checking of outer_degree
        i=len(nodes)
        put = True
        for a, outdeg in nodes:
            i -= 1
            if outdeg != i:
                put = False
        if put:
            paths.append ( [ a for a,b in nodes ] )
        
    return paths



# -- Main Method ---
def infer_paths_from_traces( traces, minfreq=MIN_CLIQUE_FREQ, minsymbols=0):
    """
    >>> infer_paths_from_traces( [list("ABAB")] )
    {2: [['A', 'B']], 1: [['B', 'A']]}
    """
    cluster = cluster_same_freq( get_successor_pairs_by_freq(traces) )
    paths = {}
    for f in sorted(cluster.keys(), reverse=True):
            
        if f >= minfreq:
            path_f = []
            for X in infer_paths_from_cliques( cluster[f] ):
                if len(X) >= minsymbols:
                    path_f.append(X)

            if len(path_f) > 0:
                paths[f] = path_f
    return paths
    
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()