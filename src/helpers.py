from networkx.drawing.nx_agraph import write_dot
from networkx.drawing.nx_agraph import to_agraph 
from IPython.display import Image
import pygraphviz as pgv

def graph(G, color="#cccccc", filename="/tmp/simple.png"):

    for u, v in G.edges:
        G[u][v]["label"] = G[u][v]["weight"]
    G.graph['graph']={'rankdir':'TD'}
    G.graph['node']={'shape':'circle'}
    G.graph['edges']={'arrowsize':'1.0'}

    A = to_agraph(G) 
    A.layout('dot')                                                                 
    A.draw(filename) 
    display(Image(filename))


    
def count_successor_pairs( T ):
    
    logger.debug("Extracting pairs for %d elements in T=%s" % ( len(T), T[:20]) ) 
    pairs = []
    partial_subtrace = T[:]
    
    while len(partial_subtrace):
        s_i = partial_subtrace.pop(0)
        pairs += [ (s_i, s_i) ] + [ (s_i, s_j) for s_j in partial_subtrace ]

    logger.debug("Pairs for found = %d" % ( len(pairs) ) ) 
    return pairs