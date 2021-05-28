# Theory based on 2021-05 ideas: removing cliques

import pandas as pd
import networkx as nx
import logging
import random

logger = logging.getLogger()
cliques = nx.algorithms.clique.find_cliques


MAGIC_MAX_CLICKES = 50000

MAGIC_CHUNK_CURLS=500



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


def pairs_in_trace(Trace, cardinality=pair_cardinality):
    logging.debug(f'NEW Trace: size={len(Trace)}')
    Pairs_in_T = {}

    # Fill freq table
    
    freq_of_char = {}
    for a in Trace:
        freq_of_char[a] = freq_of_char.get(a, 0) + 1    
    logging.debug('The frequencies found are {} '.format( set(freq_of_char.values()) ))
        
    # split the trace in a hash table, identified by frequency. 
    # This step preserves order but reduces trace size.
    
    hashTrace = {}
    for a in Trace:
        f = freq_of_char[a]
        hashTrace[f] = hashTrace.get(f, []) + [a] if type(a)!=type([]) else a
        
    # For each sliced trace compute all positive pairs
    for f, T in hashTrace.items():
#         logging.debug(f'Trace={T}')
        
        # Below is the old algorithm, but restricted to same freq symbols.

        # The alphabet in T
        Sigma = list(set( [x for x in T] ))
    
        for i in range( len(Sigma) ):
            a = Sigma[i]

            Pairs_in_T[ (a,a) ] = cardinality(a, a, T)
            for b in Sigma[i+1:]:
                Pairs_in_T[ (a,b) ] = cardinality(a, b, T)
                # asymmetric paired property: if (a,b) is paired in T the (b,a) is not
                if Pairs_in_T[ (a,b) ]>=0:
                    Pairs_in_T[ (b,a) ] = -1  
                else: 
                    Pairs_in_T[ (b,a) ] = cardinality(b, a, T)

        logging.debug(f'Size of slice f={f}: {len(T)}, with {len(set(T))} unique symbols.')

    logging.debug(f'Total pairs for the whole Trace = {len(Pairs_in_T)}')
    return Pairs_in_T



# Pair graphs class
class pairDiGraph( nx.DiGraph ):
    
    # Main result
    def __add__(self,other):
        if type(self) != type(other):
            raise Exception('second argument is not a {}'.format(type(self)))
            
        H = self.copy()

        for a,b in self.edges:
            # Case: (a,b) is not pair in other but at least one symbol appear.
            if (a,b) not in other.edges and (a in other or b in other) :
                # then remember (a,b) is not a pair 
                H.add_edge(b, a, weight=-1 )
                H[a][b]['weight'] = -1

        for a,b in other.edges:
            # Case: (a,b) is not pair in H but at least one symbol appear in H.
            if (a,b) not in self.edges and (a in self or b in self) :
                # then remember (a,b) is not a pair 
                H.add_edge(a, b, weight=-1 )
                H.add_edge(b, a, weight=-1 )
                
            # Case: (a,b) appears just there , not here
            elif (a,b) not in self.edges and not (a in self or b in self) :
                # then simply transfer to here 
                H.add_edge(a, b, weight=other[a][b]['weight'] )
                

            # Case: (a,b) is pair in both graphs. 
            else:
                # then add weights, taking care of infinity
                if min(self[a][b]['weight'], other[a][b]['weight']) >= 0:
                    H[a][b]['weight'] += other[a][b]['weight']
                else:
                    H[a][b]['weight'] = -1

        H.add_nodes_from(other)
        H.addPd()
        return H  
    
    
    def addPd(self):
        self.pd = pd.DataFrame.from_dict( 
        {(u, v): int(d['weight']) for (u, v, d) in self.edges(data=True)},
        orient='index', 
        columns=['pairs'] 
    )
        
    def positive(self):
        P = self.pd[ self.pd['pairs'] > 0 ].to_dict()['pairs']
        G = _graph_from_dict(P, weights=True)
        G.add_nodes_from(self)
        G.addPd()
        return G
    


def _graph_from_dict(P, weights=False):
    G=pairDiGraph()
    for (a,b), n in P.items():
        if weights:
            G.add_edge(a, b, weight=n)
        else:
            G.add_edge(a, b)
    if weights:
        G.addPd()
    return G


def positive_graph(T, cardinality=pair_cardinality):
    if type(T) == type(''):
        return positive_graph(list(T.strip()))
    P = pandasPair( pairs_in_trace(T, cardinality=cardinality)  )
    Ppos = P[ P ['pairs'] >= 0 ].to_dict()['pairs']
    G = _graph_from_dict(Ppos, weights=True)
    G.add_nodes_from(T)
    G.addPd()
    return G


def n_layer(G, n):
    P = G.pd[ G.pd['pairs'] == n ].to_dict()['pairs']
    G = _graph_from_dict(P)
    return G


# Cliques and sequences

def cliques_from_layer(G):
    CliqueSet = list( nx.algorithms.clique.find_cliques( G.to_undirected() ) )
    return CliqueSet

def induced_graph(G, nodes):
    indG = G.copy()

    # remove the nodes not in this clique 
    for node in set(G.nodes).difference( set(nodes) ):
        indG.remove_node(node)   
    return indG
    
    
# 2021-05-28 ... removing cliques in favour of components
def sequences_in_nlayer(Glayer):
    components = nx.connected_components(Glayer.to_undirected())
    layer_seqs = []
    
    for component in components:
        Gc=induced_graph(Glayer, component)
        sorted_degrees = sorted(Gc.in_degree(), key=lambda u: u[1], reverse=False) 

        # {0: ['a'], 1: ['Y', 'X'], 2: ['1', '2'], 5: ['b']}
        mydic={}
        for n, deg in sorted_degrees:
            mydic[deg] = mydic.get(deg, []) + [n]
            
        seq = []
        for deg, e in sorted(mydic.items(), key=lambda u: u[0]):
            if len(e)==1:
                # Append as a single element
                seq.append(e[0])
            else:
                # Append as concurrent set of elements
                seq.append(set(e))

        layer_seqs.append(seq)

    return layer_seqs

# Main result
def base_sequences(G, smoothing=0):
    seqs = {}

    # Just positive layers!
    unique_layers = G.pd[ G.pd['pairs']>smoothing ]['pairs'].unique()
    logger.info(f'unique layers={unique_layers}')

    for n in sorted(unique_layers, reverse=True):
    
        logger.info('- Looking for layer={}'.format(n))

        Glayer =  n_layer(G, n)
        layer_seqs = sequences_in_nlayer(Glayer)
        if len(layer_seqs):
            seqs[n] = layer_seqs
            
        logger.info(f'-- Sequences obtained: {len(layer_seqs)}')
            
    return seqs
        
# Alias
sequences_from_positive_graph = base_sequences 
sequences_from_graph = base_sequences 

def sum_of_graphs_list(L):
    Gp = positive_graph('')
    for Ti in L:
        Gp = Gp + positive_graph(Ti)
    return Gp



def sequences_from_log( L, smoothing=0 ):
    return sequences_from_positive_graph( sum_of_graphs_list(L), smoothing=smoothing )



# def disjoint_sequences(seqs):
#     # Search sequences in the set
#     # sequences_from_log(seqs) = { freq: [], freq:[], ... }
#     minorseqs = [seq for _, seqs in sequences_from_log(seqs, smoothing=0).items() for seq in seqs]    
    
#     # Sanity check...
#     foundsymbols=[s for seq in minorseqs for s in seq]
#     otherseqs=[ [s for s in seq if s not in foundsymbols] for seq in seqs ]
#     if len( sequences_from_log(otherseqs, smoothing=0) ) > 0:
#         raise ValueError(f'I was expecting 0 but I found these symbols out of sequences: {sequences_from_log(otherseqs, smoothing=0)}')
    
#     # I got a fixed point. Stop.
#     if sorted(seqs) == sorted(minorseqs):
#         assert len(foundsymbols) == len(set(foundsymbols))
#         return seqs
#     else:
#         logger.info('Doing another disjoint search, {} seqs were removed '.format( len(seqs)-len(minorseqs) ))
#         return disjoint_sequences(minorseqs)

    
# def recursive_disjoints(seqs, chunksize, verbose=False):
#     if len(seqs) < chunksize:
#         return disjoint_sequences(seqs)
#     else:
#         limit = int(len(seqs)/2)
#         a = recursive_disjoints(seqs[:limit], chunksize, verbose=verbose)
#         b = recursive_disjoints(seqs[limit:], chunksize, verbose=verbose)
#         verbose and print(f'-- recursive_disjoints called again because {len(seqs)} > {chunksize}')

#         return disjoint_sequences(a+b)

    
# def base_sequences( G, smoothing=1, verbose=False, partition=False ):
#     disjointed = {}
#     for f, seqs in sequences_from_positive_graph( G, smoothing=smoothing ).items():
#         logger.debug(f'Calculating disjoints for layer {f}')
        
#         if len(seqs) > 1000:

#             if verbose:
#                 print(f'-- Layer {f}: Behold! I found {len(seqs)} sequences!')

#         # CLAIM: I can partition the sequence set and obtain the same result, but destroying several pairs!
            
#         if not partition:
#             s2 = disjoint_sequences(seqs)
#         else:
#             random.shuffle(seqs)
#             s2 = recursive_disjoints(seqs, MAGIC_CHUNK_CURLS, verbose=verbose)

#         if sorted(s2)!=sorted(seqs):
#             logger.info(f'Layer {f}, {len(seqs)-len(s2)} curly sequences removed')
#             if verbose:
#                 print(f'-- Layer {f}: {len(seqs)-len(s2)} curly sequences removed')

#         if len(s2):
#             disjointed[f] = s2
            
#         if verbose:
#             print(f'Layer {f}: found {len(s2)} sequences')
            
#     return disjointed
            
    
# Helpers

def pandasPair(P):
    return  pd.DataFrame.from_dict( 
        { (a[0],a[1]):b for a,b in P.items() }, 
        orient='index', 
        columns=['pairs'] 
    )

