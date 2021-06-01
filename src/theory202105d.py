# Theory based on theory C: in degree criteria, base and sequences diffrentiation

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
        #!TODO: Check right inheritance
        if type(self) != type(other):
            raise Exception('second argument {} is not a {}'.format(type(other), type(self)))
            
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
def sequences_in_nlayer(G):
    """Returns all sequences of the serialized trace from G

    Iterates over each component of G. Compare observed degrees with a theoretical serial sequence (0..N)
    If the (0..N) is not met, merge de nodes in the same set.
    Returns the sequence of the serialized trace [a,b,c,d] -> [{a}, {b,c}, {d}]
    Example: 
        Trace 'aMNOcXYaNOMcYX'  generated by the base: {a} {NMO} {c} {XY}

        ['a', 'N', 'O', 'c', 'X'], ['a', 'N', 'O', 'c', 'Y'], ['a', 'M', 'c', 'Y'], ['a', 'M', 'c', 'X'] # clique seqs
        [{'a'}, {'N', 'O', 'M'}, {'c'}, {'Y', 'X'}]  # sequences of serialized trace
    
    Algorithm sketch
        [('a', 0), ('N', 1), ('M', 1), ('O', 2), ('c', 4), ('X', 5), ('Y', 5)] # observed degrees
        [('a', 0), ('N', 1), ('M', 2), ('O', 3), ('c', 4), ('X', 5), ('Y', 6)] # theoretical serial sequence
      {},{ a      },{N        ,M        ,O      },{c      },{X        ,Y       }  # Set assignment
    """
    components = nx.connected_components(G.to_undirected())
    layer_seqs = []
    
    for component in components:
        Gc=induced_graph(G, component)
        observed_degrees = sorted(Gc.in_degree(), key=lambda u: u[1], reverse=False) 

        setSymbol, seq = set(), []
        for (symbol, observed_deg), theoretical_deg in zip( observed_degrees, range(len(observed_degrees)) ):
            if observed_deg == theoretical_deg:
                seq.append( setSymbol )
                setSymbol = set()
            setSymbol.add(symbol)
        seq.append( setSymbol )
        layer_seqs.append(seq[1:]) # The first is the empty set

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
sequences_from_positive_graph = base_sequences #TODO: Add deprecated warning
sequences_from_graph = base_sequences 

def sum_of_graphs_list(L):
    Gp = positive_graph('')
    for Ti in L:
        Gp = Gp + positive_graph(Ti)
    return Gp



def sequences_from_log( L, smoothing=0 ):
    return sequences_from_positive_graph( sum_of_graphs_list(L), smoothing=smoothing )



            
    

def pandasPair(P):
    return  pd.DataFrame.from_dict( 
        { (a[0],a[1]):b for a,b in P.items() }, 
        orient='index', 
        columns=['pairs'] 
    )


class TraceGraph:
    G = positive_graph('')
    __smoothing = 0
    __sequences = None

    def __init__(self, Log=[], graph=G):
        if len(Log):
            self.fit(Log)
        elif graph:
            self.G = graph
    
    @property
    def weigthed_sequences(self):
        if not self.__sequences:
            self.__sequences = sequences_from_graph(self.G, self.__smoothing)
        return self.__sequences
    
    @property
    def sequences(self):
        return [s for seqs in self.weigthed_sequences.values() for s in seqs]

    def fit(self, Log):
        """Add a new log of traces to self.G
        """
        self.__sequences = None
        for trace in Log:
            self.G = self.G + positive_graph(trace)
        return self

    def use(self, G):
        self.G = G

    def set_smoothing(self, smoothing=0):
        self.__smoothing = smoothing
        self.__sequences = None


            

# Conformance Checker
# Write instructions below
class ConformanceCheck(TraceGraph):
    
    def predict(self, trace, smoothing=0):
        """checks that the sequence invariants appear in trace
        
        Rationale:
            model sequences must appear in trace sequences
            Complexity is because mixing sets and lists...
        """        
        if smoothing > 0:
            self.set_smoothing(smoothing)
        # Reverse index symbol: seq_index
        rev_index = { s:i for i in range(len(self.sequences)) for s in serialize(self.sequences[i]) }
        logger.debug(f'Generated reversed index of {len(self.sequences)} sequences')

        # Concatenate all symbols of the sequences
        any_sequence = list(set(rev_index.keys()) )
        logger.debug(f'Generated any_sequence len= {len(any_sequence)}')

        T, remainder, failed_seqs = list(trace)[:], [], []
        while len(T):
            # Next symbol
            symbol, T, failed = str(T[0]), T[1:], False
            logger.debug(f'-- Next symbol  (remainder = {len(T)})')

            found_index = rev_index.get(symbol, -1)
            # if symbol not in any_sequence:
            if found_index == -1:
                # Remove the symbol in trace and continue
                T = [e for e in T if e != symbol]
            else:
                # found_index = rev_index[symbol]
                found_seq = self.sequences[ found_index ]
                logger.debug('{symbol} is in {found_seq}')

                sym_in_found_seq = set(serialize(found_seq))

                # Restricts the trace to symbols in found_seq
                subT = [symbol] + [e for e in T if e in sym_in_found_seq]
                
                # Removes found_seq from T for the next iteration of main WHILE.
                T    = [e for e in T if e not in sym_in_found_seq]

                if not failed:
                    # TEST 1: all symbols are in both sequences 
                    # But, serialized! not with sets inside.
                    if len(subT) % len(serialize(found_seq)) != 0:
                        failed = { 
                            'sequence': found_seq, 
                            'subtrace' : subT, 
                            'sequence_index' : found_index,
                            'reason' : {
                                'title' : 'new trace has less symbols than model sequence',
                                'missing' : 'TO DO!'
                            }
                        }

                if not failed:
                    # # TEST 2: Order are correct, including repetitions
                    reached_an_ERR, last_valid_symbol, stack = False, None, subT[:]
                    while len(stack) > 0:
                        for setSymbol in found_seq:
                            # not_an_error_yet and print(f'Analyzing {setSymbol} of {found_seq}')
                            for symbol in setSymbol:
                                if not reached_an_ERR:
                                    # print(f'look {symbol} in stack={stack}')
                                    # if symbol is anywhere forward
                                    if symbol in stack[0:len(setSymbol)]:
                                        # Analyzing {'2', '1'} of [{'A'}, {'2', '1'}, {'B'}]
                                        # look 2 in stack=['1', '2', 'B']
                                        # look 1 in stack=['1', 'B']
                                        last_valid_symbol = symbol
                                        stack = [s for s in stack[0:len(setSymbol)] if s!=symbol] + stack[len(setSymbol):]
                                    else:
                                        reached_an_ERR = True
                                        stack = []
                                        # print(f'{symbol} not in {stack[0:len(setSymbol)]} !!!')

                    if reached_an_ERR:
                        # failed = { 'sequence': found_seq, 'subtrace' : subT, 'sequence_index' : found_index }
                        failed = { 
                            'sequence': found_seq, 
                            'subtrace' : subT, 
                            'sequence_index' : found_index,
                            'reason' : {
                                'title' : 'The order of subtrace is incorrect',
                                'last_valid' : last_valid_symbol
                            }
                        }

            if failed:
                failed_seqs.append(failed)

        self._failed_seqs = failed_seqs
        return len(failed_seqs) == 0    

# def symbols_in_seq(S):
#     symbols = set()
#     if S:
#         for s in S:
#             if type(s) == set:
#                 symbols = symbols.union(s)
#             else:
#                 symbols.add(s)
#     return symbols

def serialize(X):
    ser = []
    for x in X:
        if type(x) != set and type(x) != list:
            ser.append( str(x) )
        else:
            ser = ser + serialize(x)
    return ser
