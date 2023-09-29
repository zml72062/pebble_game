import numpy as np
from typing import Tuple, Optional, List, Union
import networkx as nx

def unique(edge_index: np.ndarray, num_nodes: int) -> np.ndarray:
    """
    Take a (2, num_edges) array as input, remove duplicate edges and return
    the resulting edge_index.
    """
    row, col = edge_index
    out_1d = np.unique(row * num_nodes + col)
    _, row_ = np.unique(out_1d // num_nodes, return_inverse=True)
    _, col_ = np.unique(out_1d % num_nodes, return_inverse=True)
    return np.stack([row_, col_])

def maybe_num_nodes(edge_index: np.ndarray, num_nodes: Optional[int] = None) -> int:
    return num_nodes if num_nodes is not None else edge_index.max() + 1

def contract(edge_index: np.ndarray, nodes: Tuple[int, int],
             num_nodes: Optional[int] = None) -> np.ndarray:
    """
    Contract two nodes in a graph.
    """
    num_nodes = maybe_num_nodes(edge_index, num_nodes)
    node1, node2 = nodes
    edge_index_ = edge_index.copy()
    edge_index_[edge_index_ == node1] = node2
    return unique(edge_index_, num_nodes)

def is_clique(edge_index: np.ndarray, 
              num_nodes: Optional[int] = None) -> bool:
    return all_contract_pair(edge_index, num_nodes).shape[1] == 0

def all_contract_pair(edge_index: np.ndarray, 
                      num_nodes: Optional[int] = None) -> np.ndarray:
    num_nodes = maybe_num_nodes(edge_index, num_nodes)
    row, col = edge_index
    nodes = np.arange(num_nodes)
    col_, row_ = np.meshgrid(nodes, nodes)
    mesh = row_ * num_nodes + col_
    mesh[nodes, nodes] = 0
    out1d = np.setdiff1d(np.unique(mesh.reshape(-1))[1:], row * num_nodes + col)
    return np.stack([out1d // num_nodes, out1d % num_nodes])

def all_contract_pair_wo_order(edge_index: np.ndarray,
                               num_nodes: Optional[int] = None) -> np.ndarray:
    out2d = all_contract_pair(edge_index, num_nodes)
    row, col = out2d
    return out2d[:, row < col]

def is_isomorphic(edge_index1: np.ndarray, edge_index2: np.ndarray) -> bool:
    graph1 = nx.Graph()
    graph1.add_edges_from(edge_index1.T)
    graph2 = nx.Graph()
    graph2.add_edges_from(edge_index2.T)
    return nx.isomorphism.is_isomorphic(graph1, graph2)

def contract_once(edge_index: Union[np.ndarray, List[np.ndarray]],
                  num_nodes: Optional[int] = None) -> List[np.ndarray]:
    if isinstance(edge_index, np.ndarray):
        edge_index = [edge_index]
    num_nodes = max([maybe_num_nodes(ei, num_nodes) for ei in edge_index])
    output: List[np.ndarray] = []
    for ei in edge_index:
        pairs = all_contract_pair_wo_order(ei, num_nodes)
        for n2, n1 in pairs.T:
            result = contract(ei, (n1, n2))
            if not any([is_isomorphic(result, g) for g in output]):
                output.append(result)
    return output

def contract_all(edge_index: Union[np.ndarray, List[np.ndarray]],
                 num_nodes: Optional[int] = None) -> List[np.ndarray]:
    if isinstance(edge_index, np.ndarray):
        edge_index = [edge_index]
    num_nodes = max([maybe_num_nodes(ei, num_nodes) for ei in edge_index])
    outputs: List[List[np.ndarray]] = []
    output: List[np.ndarray] = edge_index
    while True:
        outputs.append(output)
        if len(output) == 1 and is_clique(output[0]):
            break
        output = contract_once(output)
    return sum(outputs, start=[])

