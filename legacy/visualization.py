"""
Warehouse Graph Visualization Module

Handles visualization of warehouse graphs with different edge types and node colors.
"""

import matplotlib.pyplot as plt
import networkx as nx


def visualize_warehouse_graph(G, locs, title="Warehouse Graph Structure", figsize=(16, 12)):
    """
    Visualize the warehouse graph with colored nodes and edges.
    
    Args:
        G: NetworkX graph
        locs: DataFrame with location data
        title: Plot title
        figsize: Figure size tuple
    """
    pos = {n: (G.nodes[n]['x'], G.nodes[n]['y']) for n in G.nodes}
    
    # Color nodes by vertical aisle
    v_aisle_colors = [G.nodes[n]['v_aisle'] for n in G.nodes]
    node_colors = ['red' if v == -1 else plt.cm.tab20(v % 20) for v in v_aisle_colors]
    
    # Categorize edges for visualization
    intra_aisle_edges = []
    cross_aisle_edges = []
    connector_edges = []
    
    for a, b in G.edges():
        a_v = G.nodes[a]['v_aisle']
        b_v = G.nodes[b]['v_aisle']
        a_h = G.nodes[a]['h_aisle']
        b_h = G.nodes[b]['h_aisle']
        
        # Same vertical or horizontal aisle = intra-aisle
        if (a_v == b_v and a_v >= 0) or (a_h == b_h and a_h >= 0):
            intra_aisle_edges.append((a, b))
        # Different aisles but both are intersections = cross-aisle
        elif a_v >= 0 and b_v >= 0 and a_h >= 0 and b_h >= 0:
            cross_aisle_edges.append((a, b))
        # One or both are isolated = connector
        else:
            connector_edges.append((a, b))
    
    plt.figure(figsize=figsize)
    
    # Draw different edge types with different styles
    nx.draw_networkx_edges(G, pos, edgelist=intra_aisle_edges, alpha=0.6, width=2, 
                          edge_color='blue', label='Intra-aisle')
    nx.draw_networkx_edges(G, pos, edgelist=cross_aisle_edges, alpha=0.8, width=3, 
                          edge_color='green', label='Cross-aisle (intersections)')
    nx.draw_networkx_edges(G, pos, edgelist=connector_edges, alpha=0.4, width=1.5, 
                          edge_color='gray', style='dashed', label='Connectors')
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.8, 
                          edgecolors='black', linewidths=1.5)
    nx.draw_networkx_labels(G, pos, font_size=7, font_weight='bold')
    
    plt.title(f'{title}\n(Same color = same vertical aisle, Red = isolated nodes)\n'
             'Blue=Intra-aisle, Green=Cross-aisle, Gray=Connectors', fontsize=12)
    plt.legend(loc='upper right')
    plt.axis('equal')
    plt.tight_layout()
    plt.show()


def print_edge_summary(G):
    """Print summary of edge types in the graph."""
    # Categorize edges
    intra_aisle_edges = []
    cross_aisle_edges = []
    connector_edges = []
    
    for a, b in G.edges():
        a_v = G.nodes[a]['v_aisle']
        b_v = G.nodes[b]['v_aisle']
        a_h = G.nodes[a]['h_aisle']
        b_h = G.nodes[b]['h_aisle']
        
        if (a_v == b_v and a_v >= 0) or (a_h == b_h and a_h >= 0):
            intra_aisle_edges.append((a, b))
        elif a_v >= 0 and b_v >= 0 and a_h >= 0 and b_h >= 0:
            cross_aisle_edges.append((a, b))
        else:
            connector_edges.append((a, b))
    
    print(f"Edge Types: {len(intra_aisle_edges)} intra-aisle, "
          f"{len(cross_aisle_edges)} cross-aisle, "
          f"{len(connector_edges)} connectors")


def print_graph_summary(G):
    """Print summary statistics about the graph."""
    print(f"\nGraph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, "
          f"connected={nx.is_connected(G)}")
    
    # Check connectivity
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        print(f"Warning: {len(components)} disconnected components")
