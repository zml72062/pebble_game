from game_search import GameSearcher
from itertools import product
from count_fwl import kfwl_operation
from homo import contract_all

tags = {
    'P_uu': 1,
    'P_vv': 2,
    'L_u': 3,
    'L_v': 4,
    'G_u': 5,
    'G_v': 6,
    'P_vu': 7,
    'LFWL': 8,
    'SLFWL': 9,
    'FWL': 10,
}

def P_uu(searcher: GameSearcher):
    return (lambda state: (searcher.pebbled_node(state, 0), ),
            lambda state, node: 
            kfwl_operation(searcher.builder, state, 1, node, tag=tags['P_uu']))

def P_vv(searcher: GameSearcher):
    return (lambda state: (searcher.pebbled_node(state, 1), ),
            lambda state, node: 
            kfwl_operation(searcher.builder, state, 0, node, tag=tags['P_vv']))

def L_u(searcher: GameSearcher):
    return (lambda state: tuple(searcher.neighbor_of(searcher.pebbled_node(state, 1))),
            lambda state, node: 
            kfwl_operation(searcher.builder, state, 1, node, tag=tags['L_u']))

def L_v(searcher: GameSearcher):
    return (lambda state: tuple(searcher.neighbor_of(searcher.pebbled_node(state, 0))),
            lambda state, node: 
            kfwl_operation(searcher.builder, state, 0, node, tag=tags['L_v']))

def G_operation(searcher: GameSearcher, state_id, pebble_id, node, tag = 0):
    operation = [('expand', pebble_id),
                 ('restrict', pebble_id, node)]
    return searcher.builder.composite(state_id, operation, tag=tag)

def G_u(searcher: GameSearcher):
    return (range(searcher.num_nodes),
            lambda state, node: 
            G_operation(searcher, state, 1, node, tag=tags['G_u']))

def G_v(searcher: GameSearcher):
    return (range(searcher.num_nodes),
            lambda state, node: 
            G_operation(searcher, state, 0, node, tag=tags['G_v']))

def P_vu_operation(searcher: GameSearcher, state_id, tag = 0):
    u, v = searcher.pebbled_node(state_id, 0), searcher.pebbled_node(state_id, 1)
    operation = [('restrict', searcher.num_pebbles - 1, u),
                 ('expand', 0),
                 ('restrict', 0, v),
                 ('expand', 1),
                 ('restrict', 1, searcher.pebbled_node(state_id, searcher.num_nodes - 1)),
                 ('expand', searcher.num_pebbles - 1)]
    return searcher.builder.composite(state_id, operation, tag=tag)

def P_vu(searcher: GameSearcher):
    return ((-1, ),
            lambda state, _: P_vu_operation(searcher, state, tag=tags['P_vu']))

def LFWL(searcher: GameSearcher):
    return (lambda state: product(searcher.neighbor_of(searcher.pebbled_node(state, 1)),
                                  range(2)),
            lambda state, node, pebble: 
            kfwl_operation(searcher.builder, state, pebble, node, tag=tags['LFWL']))

def SLFWL(searcher: GameSearcher):
    return (lambda state: product(list(searcher.neighbor_of(searcher.pebbled_node(state, 0))) + 
                                  list(searcher.neighbor_of(searcher.pebbled_node(state, 1))),
                                  range(2)),
            lambda state, node, pebble: 
            kfwl_operation(searcher.builder, state, pebble, node, tag=tags['SLFWL']))

def FWL(searcher: GameSearcher):
    return (lambda state: product(range(searcher.num_nodes),
                                  range(2)),
            lambda state, node, pebble: 
            kfwl_operation(searcher.builder, state, pebble, node, tag=tags['FWL']))

def multiple_selection(searcher: GameSearcher, prompts):
    arg_space = {prompt: eval(prompt)(searcher)[0] for prompt in prompts}

    def arg(state):
        args = []
        for prompt in prompts:
            try:
                args += list(product([prompt], arg_space[prompt](state)))
            except:
                args += list(product([prompt], arg_space[prompt]))
        return args

    func_dict = {prompt: eval(prompt)(searcher)[1] for prompt in prompts}

    def func(state, prompt, *args):
        args, = args
        if isinstance(args, tuple):
            return func_dict[prompt](state, *args)
        return func_dict[prompt](state, args)
    return arg, func

def can_local_fwl2_count_colorful(edge_index, mode, num_nodes = None):
    searcher = GameSearcher(edge_index, 3, num_nodes)

    # Initialization step
    if mode[0] == 'VS':
        searcher.search(range(searcher.num_nodes),
                        lambda state, node:
                        searcher.builder.restrict(state, 0, node))
        searcher.search(range(searcher.num_nodes),
                        lambda state, node:
                        searcher.builder.restrict(state, 1, node))
    elif mode[0] == 'SV':
        searcher.search(range(searcher.num_nodes),
                        lambda state, node:
                        searcher.builder.restrict(state, 1, node))
        searcher.search(range(searcher.num_nodes),
                        lambda state, node:
                        searcher.builder.restrict(state, 0, node))
        
    # Game step
    mode = mode[1:]
    while searcher.state_set.shape[0] > 0:
        searcher.search(*multiple_selection(searcher, mode))

    return searcher.can_spoiler_win()

SWL_VS = ['VS', 'L_u']
SWL_SV = ['SV', 'L_u']
PSWL_VS = ['VS', 'L_u', 'P_vv']
PSWL_SV = ['SV', 'L_u', 'P_vv']
GSWL = ['VS', 'L_u', 'G_v']
SSWL = ['VS', 'L_u', 'L_v']
LFWL_2 = ['VS', 'LFWL']
SLFWL_2 = ['VS', 'SLFWL']
FWL_2 = ['VS', 'FWL']

def can_local_fwl2_count(edge_index, mode, num_nodes = None):
    return all([can_local_fwl2_count_colorful(g, mode)
                for g in contract_all(edge_index, num_nodes)])
