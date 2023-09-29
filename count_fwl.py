from cc import GameBuilder
from game_search import GameSearcher
from itertools import product
from homo import contract_all

def kfwl_operation(builder: GameBuilder, state_id,
                   old_pebble_id, new_pebble_place, tag = 0):
    """
    A composite operation:
        - Place the (k+1)-th pebble at "new_pebble_place"
        - Remove the "old_pebble_id"-th pebble
        - Place the "old_pebble_id"-th pebble to the place of
          the (k+1)-th pebble
        - Remove the (k+1)-th pebble
    """
    operation = [('restrict', builder.num_pebbles - 1, new_pebble_place),
                 ('expand', old_pebble_id),
                 ('restrict', old_pebble_id, new_pebble_place),
                 ('expand', builder.num_pebbles - 1)]
    return builder.composite(state_id, operation, tag=tag)

def can_kfwl_count_colorful(edge_index, k, num_nodes = None):
    searcher = GameSearcher(edge_index, k + 1, num_nodes)

    # Initialization step
    for i in range(k):
        searcher.search(range(searcher.num_nodes),
                        lambda state, node:
                        searcher.builder.restrict(state, i, node))
        
    # Game step
    while searcher.state_set.shape[0] > 0:
        searcher.search(product(range(searcher.num_nodes),
                                range(searcher.num_pebbles - 1)),
                        lambda state, node, pebble:
                        kfwl_operation(searcher.builder, state, pebble, node))

    return searcher.can_spoiler_win()

def can_kfwl_count(edge_index, k, num_nodes = None):
    return all([can_kfwl_count_colorful(g, k) 
                for g in contract_all(edge_index, num_nodes)])
        
    