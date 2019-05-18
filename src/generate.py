import networkx as nx
from typing import List, Dict, Tuple
import random
import numpy as np
import logging

from src.LightMultiGraph import LightMultiGraph
from src.Rule import PartRule
from src.globals import find_boundary_edges

def generate_graph(rule_dict: Dict[int, List[PartRule]]) -> Tuple[LightMultiGraph, List[int]]:
    """
    Create a new graph from the VRG at random
    :return: newly generated graph
    """
    node_counter = 1

    new_g = LightMultiGraph()
    new_g.add_node(0, label=0)

    non_terminals = {0}
    rule_ordering = []  # list of rule ids in the order they were fired

    while len(non_terminals) > 0:      # continue until no more non-terminal nodes
        node_sample = random.sample(non_terminals, 1)[0]  # choose a non terminal node at random
        lhs = new_g.nodes[node_sample]['label']

        rhs_candidates = rule_dict[lhs]

        if len(rhs_candidates) == 1:
            rhs = rhs_candidates[0]
        else:
            weights = np.array([rule.frequency for rule in rhs_candidates])
            weights = weights / np.sum(weights)   # normalize into probabilities
            idx = int(np.random.choice(range(len(rhs_candidates)), size=1, p=weights))  # pick based on probability
            rhs = rhs_candidates[idx]

        logging.debug(f'firing rule {rhs.id}, selecting node {node_sample} with label: {lhs}')
        rule_ordering.append(rhs.id)

        broken_edges = find_boundary_edges(new_g, {node_sample})
        assert len(broken_edges) == lhs

        new_g.remove_node(node_sample)
        non_terminals.remove(node_sample)

        nodes = {}

        for n, d in rhs.graph.nodes(data=True):   # all the nodes are internal
            new_node = node_counter
            nodes[n] = new_node

            label = None
            if 'label' in d:  # if it's a new non-terminal add it to the set of non-terminals
                non_terminals.add(new_node)
                label = d['label']

            if label is None:
                new_g.add_node(new_node, b_deg=d['b_deg'])
            else:
                new_g.add_node(new_node, b_deg=d['b_deg'], label=label)
            node_counter += 1


        # randomly assign broken edges to boundary edges
        random.shuffle(broken_edges)

        # randomly joining the new boundary edges from the RHS to the rest of the graph - uniformly at random
        for n, d in rhs.graph.nodes(data=True):
            num_boundary_edges = d['b_deg']
            if num_boundary_edges == 0:  # there are no boundary edges incident to that node
                continue

            assert len(broken_edges) >= num_boundary_edges

            edge_candidates = broken_edges[: num_boundary_edges]   # picking the first num_broken edges
            broken_edges = broken_edges[num_boundary_edges: ]    # removing them from future consideration

            for u, v in edge_candidates:  # each edge is either (node_sample, v) or (u, node_sample)
                if u == node_sample:
                    u = nodes[n]
                else:
                    v = nodes[n]
                logging.debug(f'adding broken edge ({u}, {v})')
                new_g.add_edge(u, v)

        # adding the rhs to the new graph
        for u, v in rhs.graph.edges():
            edge_multiplicity = rhs.graph[u][v]['weight']  #
            new_g.add_edge(nodes[u], nodes[v], weight=edge_multiplicity)
            logging.debug(f'adding RHS internal edge ({nodes[u]}, {nodes[v]}) wt: {edge_multiplicity}')

    return new_g, rule_ordering

