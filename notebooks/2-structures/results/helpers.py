# Helper functions to draw the notebooks nicely

import networkx as nx
import matplotlib.pyplot as plt



def graph(G, color="#cccccc", with_weigths=True):
    pos = nx.circular_layout(G)
    plt.rcParams['figure.figsize'] = [10, 6]
    plt.subplot(111)

    nx.draw_networkx (G, pos, width=1, node_color=color, with_labels=True, connectionstyle='arc3, rad=0.03' )
    if with_weigths:
        weights = { (str(u), str(v)): G[u][v]['weight'] for u,v in G.edges() }
        nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=weights)
    plt.show()

def pretty( arg ):
	paths, loops, G = arg
	graph(G)
	print("Paths: \n", paths)
	print("Loops: \n", loops)