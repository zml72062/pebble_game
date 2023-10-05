"""
Search pebble game graph to decide substructure counting capability.
"""
import numpy as np
from typing import Optional, Union, Callable, Iterable
from collections import defaultdict
from cc import GameBuilder, concatenate

class AdjList:
    def __init__(self, edge_index: np.ndarray,
                 num_nodes: Optional[int] = None):
        self.num_nodes = (num_nodes if num_nodes is not None else 
                          edge_index.max() + 1)
        self.adj_dict = defaultdict(list)
        for i, j in edge_index.T:
            self.adj_dict[i].append(j)

def search_once(builder: GameBuilder, state_set: Iterable, 
                arg_set: Union[Callable, Iterable], 
                func: Callable):
    """
    "func" should support the call "func(state, *arg)", which means
    starting from "state" and traversing all possibilities when "arg"
    runs over "arg_set" or "arg_set(state)"
    """
    def as_tuple(x):
        try:
            return tuple(x)
        except:
            return (x, )
        
    def as_callable(x):
        try:
            x(0)
            return x
        except:
            return lambda s: x
        
    arg_set = as_callable(arg_set)
    return np.unique(
        concatenate([concatenate([func(state, *as_tuple(i)) for i in arg_set(state)]) 
        for state in state_set if not builder.has_visited(state)])
    )

class GameSearcher:
    def __init__(self, edge_index: np.ndarray,
                 num_pebbles: int,
                 num_nodes: Optional[int] = None):
        self.builder = GameBuilder(edge_index, num_pebbles, num_nodes)
        self.state_set = self.builder.initialize()
        self.num_nodes = self.builder.num_nodes
        self.num_pebbles = self.builder.num_pebbles

    def pebbled_node(self, state_id: int, pebble_id: int) -> int:
        return self.builder.serialize_state(state_id)[1][pebble_id]

    def neighbor_of(self, node: int) -> np.ndarray:
        row, col = self.builder.edge_index
        return col[row == node]

    def k_hop_neighbor_of(self, node: int, k: int, only: bool = True) -> np.ndarray:
        if k == 0:
            return np.array([node], dtype=np.int64)
        
        row, col = self.builder.edge_index

        node_mask = np.zeros((k+1, self.num_nodes), dtype=np.bool_)
        edge_mask = np.zeros((row.shape[0], ), dtype=np.bool_)
        
        subsets = np.array([node], dtype=np.int64)

        # let "node_mask[hop]" be nodes with distance <= hop to "node"
        for hop in range(k+1):
            node_mask[hop:, subsets] = True
            edge_mask = node_mask[hop][row]
            subsets = col[edge_mask]
        if only:
            return np.arange(self.num_nodes, dtype=np.int64)[np.diff(node_mask, axis=0)[-1]]
        return np.arange(self.num_nodes, dtype=np.int64)[node_mask[-1]]

    def search(self, arg_space, operation):
        """
        operation(state, *args)
        """
        self.state_set = search_once(self.builder,
                                     self.state_set,
                                     arg_space,
                                     operation) 
        
    def can_spoiler_win(self) -> bool:
        game_graph = AdjList(self.builder.get_game_graph())
        if_win = np.array([self.builder.is_spoiler_win(i) 
                           for i in range(game_graph.num_nodes)], dtype=np.int8)
        while True:
            diff = False
            for i in range(game_graph.num_nodes):
                if not if_win[i]:
                    state_dict = defaultdict(list)
                    for state in game_graph.adj_dict[i]:
                        state_dict[
                            (tuple(self.builder.serialize_state(state)[1]),
                             self.builder.serialize_state(state)[0])].append(state)
                    if any([np.all(if_win[v]) for v in state_dict.values()]):
                        if_win[i] = 1
                        diff = True
            if not diff:
                break
        return np.all(if_win[self.builder.initialize()])

