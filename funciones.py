def fibonacci(n):
    fib_array = [0, 1]

    for i in range(2, n):
        fib_array.append(fib_array[-1] + fib_array[-2])

    return fib_array



def floyd_warshall(graph):
    """
    Encuentra todos los caminos más cortos entre cada par de nodos en un grafo ponderado.

    :param graph: Una matriz de adyacencia representando el grafo ponderado.
                  graph[i][j] = peso de la arista de i a j, o float('inf') si no hay arista.
    :return: Una matriz de distancias mínimas entre cada par de nodos.
    """
    num_nodes = len(graph)

    # Inicializar la matriz de distancias con la misma estructura que la matriz de adyacencia.
    dist = [[float('inf') for _ in range(num_nodes)] for _ in range(num_nodes)]

    # Inicializar las distancias conocidas (diagonal principal).
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i == j:
                dist[i][j] = 0
            else:
                dist[i][j] = graph[i][j]

    # Calcular distancias mínimas.
    for k in range(num_nodes):
        for i in range(num_nodes):
            for j in range(num_nodes):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist
