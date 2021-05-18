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
    for i in range( len(Sigma_T) ):
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

# Important function!
class pairDiGraph( nx.DiGraph ):
    
    # Strong adding. 
    # Mi intuicion dice que esto se puede optimizar solo buscando los positivos
    # E inferir los 0  y los -1
    # Por ahora haré la fuerza bruta
    def __add__(self,other):
        if type(self) != type(other):
            raise Exception('second argument is not a {}'.format(type(self)))
            
        H = pairDiGraph()
        Sigma = set(self.nodes).union(set(other.nodes))
        for a in Sigma:
            for b in Sigma:
                # if the pair is broken (ab in different traces):
                if (a in self.nodes and b not in self.nodes) or \
                   (a in other.nodes and b not in other.nodes) or \
                   (b in self.nodes and a not in self.nodes) or \
                   (b in other.nodes and a not in other.nodes):
                    n1 = -1
                    n2 = -1
                # The pair can be found in at least one trace
                else:
                    try:
                        n1 = self[a][b]['weight']
                    except:
                        # (ab) not in self, then n=0
                        n1 = 0
                    try:
                        # (ab) not in other, then n=0
                        n2 = other[a][b]['weight']
                    except:
                        n2 = 0
                        
                # Add cardinalidity
                if min(n1,n2) < 0:
                    n = -1
                else:
                    n = n1 + n2
                H.add_edge(a,b,weight=n)
            
        H.pd = pd.DataFrame.from_dict( 
            { (a,b):H[a][b]['weight'] for a,b in H.edges }, 
            orient='index', 
            columns=['pairs']
        )
        return H  
                        
                    
        
#         # edges for self - other
#         H = self.copy()

#         # edges for other - self
#         Gother_only=other.subgraph( set(other.nodes).difference(set(self.nodes)) )
#         for (a,b) in Gother_only.edges:
#             H.add_edge( a, b, weight=Gother_only[a][b]['weight'] )

#         # intersection
#         common = set(self.nodes).intersection(set(other.nodes))
#         for a in common:
#             for b in common.difference(set([a])):
#                 if min( self[a][b]['weight'], other[a][b]['weight'] ) < 0:
#                     H[a][b]['weight'] = -1
#                 else:
#                     H[a][b]['weight'] = self[a][b]['weight'] + other[a][b]['weight']
            
        # Cardinality for self - other
        # Done by construction of H
        # pdG1 = self.pd

        # Cardinality for second graph
        # pdG2 = other.pd

        # Update 'self' cardinality base on the new 'other' evidence.
        # UPGRADE THIS TO USE pd.MultiIndex.from_tuples
        
#         non_negative_pairs = self.pd[ self.pd['pairs'] >= 0 ].to_dict()['pairs']
#         logger.debug('non_negative_pairs={}'.format(non_negative_pairs))
        
#         newCommonPairs = {}
#         for a,b in non_negative_pairs.keys():
#             logger.error(( a,b, non_negative_pairs[(a,b)] ))
            
#             if min( self[a][b]['weight'], other[a][b]['weight'] ) == -1:
#                 newCommonPairs[(a,b)] = -1
#             else:
#                 newCommonPairs[(a,b)] = self[a][b]['weight'] + other[a][b]['weight']
#             logger.error(( a,b, newCommonPairs[(a,b)] ))

        

        # THIS SHOULD BE REMOVED WHEN OPTIMIZE THIS FUNCTION.
        # Calculate cardinality of newly created pairs.
        # In strong adding, those are all -infty
#         newnodes = []
#         for newnode in set(other.nodes).difference(self.nodes):
#             for oldnode in self.nodes:
#                 newnodes.append( (newnode, oldnode) )
#                 newnodes.append( (oldnode, newnode) )
#                 H.add_edge(newnode, oldnode)
#                 H.add_edge(oldnode, newnode)

#         newnodesPD = pd.DataFrame.from_dict( 
#             { (a[0],a[1]):-1 for a in newnodes }, 
#             orient='index', 
#             columns=['pairs'] 
#         )
#         H.pd = pd.concat([self.pd, other.pd, newnodesPD])
#         for (a,b), card in H.pd.iterrows():
#             H[a][b]['weight'] =  card['pairs']



def _graph_from_dict(P, weights=False):
    G=pairDiGraph()
    for (a,b), n in P.items():
        if weights:
            G.add_edge(a, b, weight=n)
        else:
            G.add_edge(a, b)
    G.pd = pandasPair( P  )
    return G

def pair_graph(T, cardinality=pair_cardinality):
    if type(T) == type(''):
        return pair_graph(list(T.strip()))
    
    P = pairs_in_trace(T, cardinality=cardinality)
    G = _graph_from_dict(P, weights=True)
    return G

def non_negative_graph(G):
    P = G.pd[ G.pd['pairs'] >= 0 ].to_dict()['pairs']
    G = _graph_from_dict(P, weights=True)
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

# Main result:
def sequences_from_log( L ):
    Gp = pair_graph('')
    for Ti in L:
        Gp = Gp + pair_graph(Ti)
    return sequences_from_pair_graph( Gp )