# Theory based on 2021-05 ideas: quicker pair graphs

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

# def pair_graph(T, cardinality=pair_cardinality):
#     print('DELETE ME pair_graph')
#     if type(T) == type(''):
#         return pair_graph(list(T.strip()))
    
#     P = pairs_in_trace(T, cardinality=cardinality)
#     G = _graph_from_dict(P, weights=True)
#     return G


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
    

# Main result
def sequences_from_positive_graph(G):
    seqs = {}

    # Just positive layers!
    unique_layers = G.pd[ G.pd['pairs'] > 0 ]['pairs'].unique()
    for n in unique_layers:
        logger.debug('Looking for layer={}'.format(n))
        layer_seqs = []

        Glayer =  n_layer(G, n)

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


def sum_of_graphs_list(L):
    Gp = positive_graph('')
    for Ti in L:
        Gp = Gp + positive_graph(Ti)
    return Gp

# Main result:
def sequences_from_log( L ):
    return sequences_from_positive_graph( sum_of_graphs_list(L) )