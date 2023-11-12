import networkx as nx
import matplotlib.pyplot as plt


def drawModels(models):
    G = nx.DiGraph()
    node_colors = dict()
    edge_colors = []
    i = 1
    for model in models.values():
        print(f'{model.name} : {len(model.outgoing_deps)} outgoing deps')
        G.add_node(model.name)
        node_colors[model.name] = i 
        i += 2

    for model in models.values():
        # print(f'Adding deps for {model.name}')
        for dep in model.outgoing_deps:
            # print(f'Dep : {dep.name})')
            if dep.name not in G.nodes():
                G.add_node(dep.name)
            G.add_edge(model.name, dep.name)
            edge_colors.append(node_colors[model.name])
            if dep not in models.values():
                node_colors[dep.name] = 0
    node_colors_list = list(node_colors.values())

    coord = arcLayout(G.nodes(), models)
    printGraph(G, coord, node_colors_list, edge_colors)


def arcLayout(nodes, models):
    coord = dict()
    i = 0
    for node in nodes:
        nodename = node
        weight = 1
        if nodename in models:
            weight = models[nodename].weight
        x = i+weight
        coord[nodename] = [x, 0]
        i += 5
    return coord


def printGraph(G, coord, node_colors_list, edge_colors):
    # colormap = plt.cm.gist_rainbow
    colormap = plt.cm.twilight
    fig = plt.figure(1, figsize=(14, 10))
    # node_sizes = [(v*50) for v in d.values()]
    # coord = nx.kamada_kawai_layout(G)
    # coord = nx.shell_layout(G, rotate=1.5)
    # coord = nx.circular_layout(G)
    # coord = nx.spring_layout(G, k=1)
    nx.draw_networkx_nodes(G, coord,
                           node_color=node_colors_list,
                           cmap=colormap,
                           # node_size=node_sizes
                           )
    nx.draw_networkx_edges(G,
                           coord,
                           arrowstyle='->',
                           edge_color=edge_colors,
                           edge_cmap=colormap,
                           connectionstyle="arc3,rad=0.9",
                           arrowsize=14
                           )
    labels = nx.draw_networkx_labels(G,
                                     coord,
                                     font_size=10)
    for _, l in labels.items():
        l.set_rotation(45)

    fig.tight_layout()
    plt.show()
