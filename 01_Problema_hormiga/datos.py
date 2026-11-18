import networkx as nx
import matplotlib.pyplot as plt
import random as rd
from matplotlib.widgets import Button

def dfs():
    vecinos = list(G.neighbors((0,0)))
    for vecino in vecinos :
        if G.nodes[vecino]["obstaculo"] != True:
            print(vecino)
        


G = nx.grid_2d_graph(5, 5)
nx.set_edge_attributes(G, 1, "weight")
nx.set_node_attributes(G,False, "obstaculo")
contador = 0
while(contador < 5):
    nodo = ((rd.randint(0,4),rd.randint(0,4)))
    if nodo != (0,0) and nodo != (4,4):
        G.nodes[nodo]["obstaculo"] = True
        contador +=1            
pos = {nodo: (nodo[1], -nodo[0]) for nodo in G}
colores = [
    "green" if G.nodes[n].get("obstaculo", False) else "skyblue"
    for n in G
]
nx.draw(G, pos, with_labels=True, node_size=1000, node_color=colores)
pesos = nx.get_edge_attributes(G, "weight") #Se almacena la información del peso
nx.draw_networkx_edge_labels(G, pos, edge_labels=pesos) #se coloca la etiqueta del peso a cada arista

dfs()

plt.show()
