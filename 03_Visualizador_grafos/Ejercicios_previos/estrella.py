import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

G = nx.Graph()

G.add_edge(29, 7, weight=2)
G.add_edge(29, 21, weight=3)
G.add_edge(7, 11, weight=5)
G.add_edge(21, 11, weight=2)
G.add_edge(21, 24, weight=2)
G.add_edge(11, 24, weight=7)
G.add_edge(14, 7, weight=3)
G.add_edge(14, 11, weight=9)

#Como posicionar 
pos = nx.spring_layout(G)

#como dibujar nodos y aristas en base a el como posicionar 
nx.draw(G, pos, with_labels=True, node_size=1000)

pesos = nx.get_edge_attributes(G, "weight") #Se almacena la información del peso
nx.draw_networkx_edge_labels(G, pos, edge_labels=pesos) #se coloca la etiqueta del peso a cada arista

def iniciar(event):
    print("Iniciando Dijkstra...")

ax_boton = plt.axes([0.4, 0.02, 0.2, 0.07])
boton = Button(ax_boton, "Iniciar")

boton.on_clicked(iniciar)
plt.show()