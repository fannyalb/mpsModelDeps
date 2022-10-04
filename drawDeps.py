import networkx as nx
import matplotlib.pyplot as plt


def drawDeps(model_deps):
    G = nx.DiGraph()
    node_colors = dict()
    edge_colors = []
    i = 1
    for model in model_deps.keys():
        G.add_node(model)
        node_colors[model] = i
        i += 1

    for model in model_deps.keys():
        for dep in model_deps[model]:
            G.add_edge(model, dep)
            edge_colors.append(node_colors[model])
            if dep not in model_deps.keys():
                node_colors[dep] = 0
    node_colors_list = list(node_colors.values())

    d = dict(G.out_degree())
    colormap = plt.cm.gist_rainbow
    fig = plt.figure(1, figsize=(80, 80))
    node_sizes = [(v*50) for v in d.values()]
    # coord = nx.kamada_kawai_layout(G)
    # coord = nx.shell_layout(G, rotate=1.5)
    # coord = nx.circular_layout(G)
    # coord = nx.spring_layout(G, k=1)
    coord = arc_layout(G.nodes())
    nx.draw_networkx_nodes(G, coord,
                           node_color=node_colors_list,
                           cmap=colormap,
                           node_size=node_sizes
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


def arc_layout(nodes):
    coord = dict()
    i = 0
    for node in nodes:
        nodename = node
        coord[nodename] = [i, 0]
        i = i+3
    return coord
