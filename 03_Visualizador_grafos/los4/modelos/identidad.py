"""Identidad de una arista paralela, respetando el sentido del grafo."""
def identidad_arista(origen, destino, clave, dirigido):
    return (origen, destino, clave) if dirigido else (frozenset((origen, destino)), clave)
