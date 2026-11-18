import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()

G.add_edge(29, 7, weight=2)
G.add_edge(29, 21, weight=3)
G.add_edge(7, 11, weight=5)
G.add_edge(21, 11, weight=2)
G.add_edge(21, 24, weight=2)
G.add_edge(11, 24, weight=7)

pos = nx.spring_layout(G)

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=1000
)

pesos = nx.get_edge_attributes(G, "weight")

nx.draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=pesos
)

plt.show()