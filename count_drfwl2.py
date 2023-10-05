from game_search import GameSearcher
from itertools import product
from count_fwl import kfwl_operation
from homo import contract_all
import numpy as np

tags = {
    (0, 0): 1,
    (0, 1): 2,
    (1, 0): 3,
    (1, 1): 4,
    (0, 2): 5,
    (2, 0): 6,
    (1, 2): 7,
    (2, 1): 8,
    (2, 2): 9,
    (0, 3): 10,
    (3, 0): 11,
    (1, 3): 12,
    (3, 1): 13,
    (2, 3): 14,
    (3, 2): 15,
    (3, 3): 16,
}

def DRFWL(searcher: GameSearcher, hop1: int, hop2: int):
    return (lambda state: product(
        np.intersect1d(searcher.k_hop_neighbor_of(searcher.pebbled_node(state, 0), hop1),
                       searcher.k_hop_neighbor_of(searcher.pebbled_node(state, 1), hop2),
                       assume_unique=True),
        range(2)),
            lambda state, node, pebble: 
            kfwl_operation(searcher.builder, state, pebble, node, tag=tags[(hop1, hop2)]))

def multiple_selection(searcher: GameSearcher, prompts):
    arg_space = {prompt: DRFWL(searcher, *prompt)[0] for prompt in prompts}

    def arg(state):
        args = []
        for prompt in prompts:
            try:
                args += list(product([prompt], arg_space[prompt](state)))
            except:
                args += list(product([prompt], arg_space[prompt]))
        return args

    func_dict = {prompt: DRFWL(searcher, *prompt)[1] for prompt in prompts}

    def func(state, prompt, *args):
        args, = args
        if isinstance(args, tuple):
            return func_dict[prompt](state, *args)
        return func_dict[prompt](state, args)
    return arg, func

def can_drfwl2_count_colorful(edge_index, mode, k, num_nodes = None):
    searcher = GameSearcher(edge_index, 3, num_nodes)

    searcher.search(range(searcher.num_nodes),
                    lambda state, node:
                    searcher.builder.restrict(state, 0, node))
    searcher.search(lambda state: searcher.k_hop_neighbor_of(searcher.pebbled_node(state, 0), k, False),
                    lambda state, node:
                    searcher.builder.restrict(state, 1, node))

        
    # Game step
    while searcher.state_set.shape[0] > 0:
        searcher.search(*multiple_selection(searcher, mode))

    return searcher.can_spoiler_win()

DRFWL1 = [(0, 0), (0, 1), (1, 0), (1, 1)]
DRFWL2 = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2)]
DRFWL3 = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 2), (2, 0), (1, 2), (2, 1), (2, 2), 
          (0, 3), (3, 0), (3, 1), (3, 2), (3, 3), (2, 3), (1, 3)]

def can_drfwl2_count(edge_index, mode, k, num_nodes = None):
    return all([can_drfwl2_count_colorful(g, mode, k)
                for g in contract_all(edge_index, num_nodes)])
