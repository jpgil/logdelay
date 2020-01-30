import math
import logging
import sys
import networkx as nx
# import scipy.
import matplotlib.pyplot as plt



METHOD_ID="2020-01-25 loop"
PAIRS_ID="all"




# logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
# import logging
# logging.basicConfig(format='%(funcName)s:%(levelname)s:%(message)s', level=logging.INFO, stream=sys.stdout)



def find_loops_in_path(p, succ_G, PAIRS_ID="all"):
    """
    Write a nice doc here
    """
    if   PAIRS_ID=="partial":
        return find_loops_in_path_partialpairs(p, succ_G)
    elif PAIRS_ID=="all":
        return find_loops_in_path_allpairs(p, succ_G)

    
    
def find_loops_in_path_partialpairs(p, succ_G):
    """
    With partial pairs, if ABC is a loop in pairs of len L then 
    f(A,B) = f(B,C) = L and f(B,A) = f(C,B) = L-1
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    is_a_loop, L = False, 0

    # Check if p is a loop
    for a, b in [ (a,b) for a,b in zip( p[:-1], p[1:] )  ]:

        is_a_loop = True
        setL = set()
        if is_a_loop and (b, a) in succ_G.edges() and (a, b) in succ_G.edges():
            Wab = succ_G[a][b]['weight'] # also, Wab=f by construction
            Wba = succ_G[b][a]['weight']
            
            # L test
            """
            f(A,B) = f(B,C) = L and f(B,A) = f(C,B) = L-1
            """
            L = Wab            
            setL.add(L)
            logger.debug( (a, b, Wab, L, Wba, L-1 ))
            
            # Me falta chequear que L+1 y L-1 sean consistentes en todfo el path
            if Wba != L-1:
                is_a_loop = False
        else:
            is_a_loop = False     
            
    if is_a_loop and len(setL) != 1:
        is_a_loop = False

    return is_a_loop, L

def find_loops_in_path_allpairs(p, succ_G):
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



def remove_loops_in_trace(paths_loop, succ_G, PAIRS_ID="all"):
    """
    A loop... should be disjoint with other loops?
    I believe YES
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )

    loops_found = []
    loops_candidates = []


    # Let's try something different... looks also backwardws (it worked!)
    for f, paths_f in paths_loop.items():
        
        for path in paths_f:
            for p in [ path, list(reversed(path)) ]:
                # Magic here
                is_a_loop, L = find_loops_in_path(p, succ_G, PAIRS_ID=PAIRS_ID)

                if is_a_loop:
                    if (L,p) not in loops_candidates:
                        loops_candidates.append( (L,p) )
                        logger.info("Loop candidate FOUND: repeated %d times in this trace, loop: %s" % (L, p) )
                else:
                    logger.debug("It seems that p is not a loop: %s" % p)
                
    # # Check Loop Disjoints --- not really needed. 
    # if len(loops_candidates) == 1:
    #     loops_found = loops_candidates
    #     logger.info("My dude %s is a real %s-loop" % (loops_found[0][1], loops_found[0][0]))

    # else:

    #     # Starts with LONGEST paths first! Prove it prove it
    #     for L, path in sorted(loops_candidates, key=lambda e: -len(e[1]) ):

    #         # If path is disjoint with someone else, append both
    #         for L2, p2 in loops_candidates: # [(L2, p2) for L2, p2 in loops_candidates if p2 != path]:

    #             if path != p2:
    #                 # p2 and path are disjoints!
    #                 # path must be also disjoint with all found loops
    #                 if not set(p2).intersection( set(path) ) and \
    #                 all( [ not set(p_found).intersection( set(path) ) for Lx, p_found in loops_found] ):
    #                     logger.info("My dude %s is a real %s-loop" % (path, L))
    #                     loops_found.append((L, path))
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





def evaluate_against (T, expected_paths):
    logger = logging.getLogger( sys._getframe().f_code.co_name )

    G, paths = False, False
    
    if   METHOD_ID=="2020-01-24 all pairs":
        paths = infer_paths( split_in_freqGraph( successorsGraph(  get_successor_by_freq(T, PAIRS_ID="all")  ) ) )

        
    elif METHOD_ID=="2020-01-20 partial pairs":
        paths = infer_paths( split_in_freqGraph( successorsGraph(  get_successor_by_freq(T, PAIRS_ID="partial")  ) ) )

        
    elif METHOD_ID=="2020-01-25 loop":
        
        all_loops = {}
        G = False


        for trace in T:

            # Calculate the successors only for this trace
            succ_f = get_successor_by_freq([trace], PAIRS_ID=PAIRS_ID)
            # Put in a graph
            succ_G = successorsGraph( succ_f )

            # Detect loops first computing raw paths
            paths_loop = infer_paths( split_in_freqGraph(  succ_G  ) )
            
            loops_this_trace, succ_G_acyclic = remove_loops_in_trace(paths_loop, succ_G, PAIRS_ID=PAIRS_ID)

            for L,p in loops_this_trace:
                pt = tuple(p)
                if pt not in all_loops.keys():
                    all_loops[pt] =  float(L)
                else:
                    all_loops[pt] += float(L)
            
            # Claim: the graph should be cycle free. So, let's remove any trivial cycle AB BA not in loops!
            succ_G_acyclic_forReal = nx.DiGraph()
            E = succ_G_acyclic.edges()
            for u, v in E:
                if (v, u) not in E:
                    succ_G_acyclic_forReal.add_edge(u, v, weight=succ_G_acyclic[u][v]["weight"]  )
                else:
                    logger.debug("Removing (%s, %s)" % (u,v))

            # # Now merge the big graph of all the traces
            if not G:
                G = succ_G_acyclic_forReal.copy()
            else:
                for u,v in succ_G_acyclic_forReal.edges():
                    Gw = succ_G_acyclic_forReal[u][v]["weight"]
                    if (u,v) not in G.edges():
                        G.add_edge(u, v, weight=Gw)
                    else:
                        G[u][v]["weight"] += Gw

            # # Graph this trace
            # # Untangled trace graph: If paths (u,z,v) and (u,v) exists, leave just (u,z,v)
            # paths_this_trace = infer_paths( split_in_freqGraph(  succ_G_acyclic_forReal  ) )
            # G_trace = minimally_connected( path_graph( paths_this_trace ) )

            # # # Restore loops info
            # # for path, L in all_loops.items():
            # #     G_trace.add_edge( path[-1], path[0], weight=L )

            # graph(G_trace)



        # Get paths with the acyclic graph for all pairs      
        paths = infer_paths( split_in_freqGraph( G ) )
        G = minimally_connected( path_graph( infer_paths( split_in_freqGraph(  G  ) ) ) )
        # Restore loops info
        for path, L in all_loops.items():
            G.add_edge( path[-1], path[0], weight=L )
        graph(G)

#         paths = { 1:[] }
# #         for f, G1 in G_freq.items():
# #             paths[f] = nx.all_shortest_paths(G, "_START_", "_END_")
            
#         for path in nx.all_simple_paths(G, "_START_", "_END_"):
#             path.remove("_START_")
#             path.remove("_END_")
#             paths[1].append( path )
        

    else:
        raise ValueError("Not valid METHOD_ID")
             
            
    if paths:
        
#         G = nx.DiGraph()
#         for f, path in paths.items():
#             for a, b in [ (a,b) for t in path for a,b in zip( t[:-1], t[1:] )  ]:
#                 G.add_edge( a, b, weight=f)
#         graph(G, with_weigths=True )
        
        good = []
        bad = []
        expected = [ list(a) for a in expected_paths ]
        for f, paths in paths.items():
            for p in paths:
    #             print(paths)
                if p in expected:
                    good.append( "%d: %s" % (f, "".join(p)) )
                else:
                    bad.append( "%d: %s" % (f, "".join(p)) )

        if len(expected_paths) != len(good):
            print(), print()
            print("WARNING HERE! OJO AQUI!")
            print(), print()
        print("Loops found:")
        print(all_loops)
        print()

        print("These %s paths were correctly detected (%s undetected):" % (len(good), len(expected_paths)-len(good)))
        print(good)
        print()

        print("These %s paths are spurious:" % len(bad))
        print (bad)
        return good, bad
    else:
        return [], []








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




def graph(G, color="#cccccc", with_weigths=True):
    pos = nx.circular_layout(G)
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.subplot(111)

    nx.draw_networkx (G, pos, width=1, node_color=color, with_labels=True, connectionstyle='arc3, rad=0.03' )
    if with_weigths:
        weights = { (str(u), str(v)): G[u][v]['weight'] for u,v in G.edges() }
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=weights)
    plt.show()




def get_successor_by_freq( traces, PAIRS_ID="partial" ):
    """
    Get successor pairs in every T in traces, and combine them by frequency of appearance.
    
    >>> T = [ list("ABC"), list("ABCABC") ]
    >>> get_successor_pairs_by_freq(T)
    {('A', 'B'): 3, ('A', 'C'): 3, ('B', 'C'): 3, ('B', 'A'): 1, ('C', 'A'): 1, ('C', 'B'): 1}
    """
    logger = logging.getLogger( sys._getframe().f_code.co_name )
    logger.info("Using PAIRS_ID % s" % PAIRS_ID)
    
    pairs_with_freq = {}
    L = float(len(traces))

    for trace in traces:
        for pair in get_successor_pairs(trace, PAIRS_ID=PAIRS_ID):
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
    logger.debug("Freq  pairs using method=%s : %s" % (PAIRS_ID, By_freq) )
    return By_freq




def successorsGraph(successor_by_freq):
    G=nx.DiGraph()
    for f, pairs in successor_by_freq.items():
        for u, v in pairs:
            G.add_edge(u, v, weight=f)
            
    return G





# Sort the cliques and apply the rules:
# 1) The nodes of a single path in their equivalent pair has in_degree=0,1,2,...
# 2) A path is composed for at least 2 ... 3? nodes

def infer_paths(G_freq, min_clique_size=2):
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




# Including Modifications by Andres (20200124)
ADD_START_END = False
def get_successor_pairs( T_prime , ADD_START_END=ADD_START_END, PAIRS_ID="partial"):
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
    logger.info("Using PAIRS_ID % s" % PAIRS_ID)


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
        if PAIRS_ID == "partial":
            T_i_j=partial_subtrace[:j] # 2020-01-20 Old BEHAVIOR
        elif PAIRS_ID=="all":
            T_i_j=partial_subtrace[:] # Andres 20200124 .. all friends with all, including loops
        
        T_i_j_pairs = [] # 2020-01-23 BEHAVIOR ... but not remove, it doesn't affect

        # Construct all s_i, s_k , i < k <= j
        for s_k in T_i_j:
            e = (s_i, s_k)

            pairs.append(e)       # 2020-01-20 Old BEHAVIOR
            
#             if e not in T_i_j_pairs:  # 2020-01-23 BEHAVIOR
#                 T_i_j_pairs.append(e) # 2020-01-23 BEHAVIOR
#         pairs += T_i_j_pairs          # 2020-01-23 BEHAVIOR
            
            
            # Added 2020-01-18: global star / end
            if ADD_START_END:
                pairs.append( ("_START_", s_i) )
                pairs.append(( s_k, "_END_") )

    logger.debug("Found pairs using method=%s : %s" % (METHOD_ID, pairs) )
    return pairs






def split_in_freqGraph( successorsGraph ):
    
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