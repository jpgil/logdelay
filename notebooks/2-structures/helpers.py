import networkx as nx
import scipy
import matplotlib.pyplot as plt

from networkx.drawing.nx_agraph import write_dot
from networkx.drawing.nx_agraph import to_agraph 
from IPython.display import Image
import pygraphviz as pgv

def graph(G, color="#cccccc", filename="/tmp/simple.png"):

    for u, v in G.edges:
        if "weight" in G[u][v]:
            G[u][v]["label"] = G[u][v]["weight"]
    G.graph['graph']={'rankdir':'TD'}
    G.graph['node']={'shape':'circle'}
    G.graph['edges']={'arrowsize':'1.0'}

    A = to_agraph(G) 
    A.layout('dot')                                                                 
    A.draw(filename) 
    display(Image(filename))

# Stolen from https://stackoverflow.com/questions/12836385/how-can-i-interleave-or-create-unique-permutations-of-two-strings-without-recur/12837695
# More doc at http://www.cs.utsa.edu/~wagner/knuth/fasc2b.pdf
class Interleave():

    def __init__(self, A, B):
        self.A = A
        self.B = B
        self.results = list(self.__interleave())

    # from https://stackoverflow.com/a/104436/1561176
    def __all_perms(self, elements):
        if len(elements) <=1:
            yield elements
        else:
            for perm in self.__all_perms(elements[1:]):
                for i in range(len(elements)):
                    #nb elements[0:1] works in both string and list contexts
                    yield perm[:i] + elements[0:1] + perm[i:]

    def __sequences(self):
        return list( sorted( set(
            ["".join(x) for x in self.__all_perms(['a'] * len(self.A) + ['b'] * len(self.B))] ) ) )

    def __interleave(self):
        for sequence in self.__sequences():
            result = ""
            a = 0
            b = 0
            for item in sequence:
                if item == 'a':
                    result+=self.A[a]
                    a+=1
                else:
                    result+=self.B[b]
                    b+=1
            yield result

    def __str__(self):
        return str(self.results)

    def __repr__(self):
        return repr(self.results)


# # Function to calculate the cliques and GRAPH in one single line.
# def nice_graph( weighted_paths ):
    
#     def append_path(G, path, weight):
#         previous = path[0]
#         for node in path[1:]:
#             edges.append( (previous, node, {"weight":weight} ) )
#             previous = node
#         G.add_edges_from(edges)

 
# #     weighted_paths = clique_discovery.infer_paths_from_traces( T )
#     print(weighted_paths)
#     found_paths = {}
#     edges = []
#     G = nx.DiGraph()
    
#     # Check serial: solo disjuntos del mismo largo
#     for w in sorted(weighted_paths, reverse=True):
#         for path_w in weighted_paths[w]:
#             if w not in found_paths.keys():
#                 found_paths[w] = []
#             if all( [ not set(path_w).intersection(set(z)) for z in found_paths[w] ] ):
#                 append_path( G, path_w, w )                
                
#     weights = { (str(u), str(v)): G[u][v]['weight'] for u,v in G.edges() }

#     pos = nx.spring_layout(G)

#     plt.rcParams['figure.figsize'] = [14, 6]
#     plt.subplot(111)


#     nx.draw_networkx (G, pos, width=1, node_color="#cccccc", with_labels=True, connectionstyle='arc3, rad=0.5' )
#     nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=weights)

#     plt.show()
    
def created_auxiliary_grap( weighted_paths ):
    
    def append_path(G, path, weight):
        edges = []
        previous = path[0]
        for node in path[1:]:
            edges.append( (previous, node, {"weight":weight} ) )
            previous = node
        G.add_edges_from(edges)

    G = nx.DiGraph()
    
    # Check serial: solo disjuntos del mismo largo
    for w in sorted(weighted_paths, reverse=True):
        for path_w in weighted_paths[w]:
            append_path( G, path_w, w )              
            
    return G

# Function to calculate the cliques and GRAPH in one single line.
def nice_graph( weighted_paths, with_weigths=True ): 
    
    print(weighted_paths)

    G = created_auxiliary_grap( weighted_paths )
    try:
        G.remove_node("_START_")
        G.remove_node("_END_")
    except:
        pass

    
    weights = { (str(u), str(v)): round(G[u][v]['weight'], 2) for u,v in G.edges() }

    pos = nx.spring_layout(G)
    pos = nx.circular_layout(G)


    plt.rcParams['figure.figsize'] = [8, 4]
    plt.subplot(111)


    nx.draw_networkx (G, pos, width=1, node_color="#cccccc", with_labels=True, connectionstyle='arc3, rad=0.05' )
    if with_weigths:
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=weights)

    plt.show()
    
def untangled_graph(G, with_weigths=True):
    weights = { (str(u), str(v)): G[u][v]['weight'] for u,v in G.edges() }

    pos = nx.spring_layout(G)
    pos = nx.circular_layout(G)


    plt.rcParams['figure.figsize'] = [10, 4]
    plt.subplot(111)

    nx.draw_networkx (G, pos, width=1, node_color="#cccccc", with_labels=True, connectionstyle='arc3, rad=0.05' )
    if with_weigths:
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=weights)


    plt.show()

    