import ctypes
import numpy as np
import numpy.ctypeslib as npc
from typing import Optional, Tuple, List, Literal, Union
import os

# os.system('g++ -o cc_impl.so -fPIC -shared -std=c++11 cc_impl.cpp')
lib = ctypes.CDLL('./cc_impl.so')

get_builder = lib.get_builder
get_builder.argtypes = [
    ctypes.POINTER(ctypes.c_long),
    ctypes.c_long,
    ctypes.c_long,
]
get_builder.restype = ctypes.POINTER(ctypes.c_char)

free_builder = lib.free_builder
free_builder.argtypes = [
    ctypes.POINTER(ctypes.c_char),
]

initialize_states = lib.initialize_states
initialize_states.argtypes = [
    ctypes.POINTER(ctypes.c_char),
]
initialize_states.restype = ctypes.POINTER(ctypes.c_long)

restrict_from_state = lib.restrict_from_state
restrict_from_state.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_int,
    ctypes.c_int,
]
restrict_from_state.restype = ctypes.POINTER(ctypes.c_long)

expand_from_state = lib.expand_from_state
expand_from_state.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_long,
    ctypes.c_int,
    ctypes.c_int,
]
expand_from_state.restype = ctypes.c_long

display_state = lib.display_state
display_state.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
]
display_state.restype = ctypes.POINTER(ctypes.c_long)

mark_visited = lib.mark_visited
mark_visited.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
]

spoiler_win = lib.spoiler_win
spoiler_win.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
]
spoiler_win.restype = ctypes.c_int

has_visited = lib.has_visited
has_visited.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
]
has_visited.restype = ctypes.c_int

get_game_graph = lib.get_game_graph
get_game_graph.argtypes = [
    ctypes.POINTER(ctypes.c_char),
]
get_game_graph.restype = ctypes.POINTER(ctypes.c_long)

edge_to_cc_id = lib.edge_to_cc_id
edge_to_cc_id.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.POINTER(ctypes.c_long),
]
edge_to_cc_id.restype = ctypes.POINTER(ctypes.c_long)

free_array = lib.free_array
free_array.argtypes = [
    ctypes.POINTER(ctypes.c_long),
]

get_state = lib.get_state
get_state.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.POINTER(ctypes.c_long),
    ctypes.c_long,
    ctypes.c_long,
]
get_state.restype = ctypes.c_long

add_edge = lib.add_edge
add_edge.argtypes = [
    ctypes.POINTER(ctypes.c_char),
    ctypes.c_long,
    ctypes.c_long,
]

ptr_add = lib.ptr_add
ptr_add.argtypes = [
    ctypes.POINTER(ctypes.c_long),
    ctypes.c_long,
]
ptr_add.restype = ctypes.POINTER(ctypes.c_long)


def maybe_num_nodes(edge_index: np.ndarray, num_nodes: Optional[int] = None) -> int:
    return num_nodes if num_nodes is not None else edge_index.max() + 1

def to_edge_dict(edge_index: np.ndarray, num_nodes: Optional[int] = None) -> np.ndarray:
    num_nodes = maybe_num_nodes(edge_index, num_nodes)
    edge_dict = np.full((num_nodes * num_nodes, ), -1, dtype=np.int64)
    row, col = edge_index
    edge_dict[row * num_nodes + col] = np.arange(edge_index.shape[1], dtype=np.int64)
    return edge_dict

def read_serialized_array(array) -> np.ndarray:
    return npc.as_array(ptr_add(array, ctypes.c_long(1)), shape=(array[0], ))

def read_serialized_array_pair(array) -> Tuple[int, np.ndarray, np.ndarray]:
    return (int(array[0]),
            npc.as_array(ptr_add(array, ctypes.c_long(3)), shape=(array[1], )),
            npc.as_array(ptr_add(array, ctypes.c_long(3 + array[1])), shape=(array[2], )))

def read_serialized_array_with_data_proprietorship(array) -> np.ndarray:
    result = read_serialized_array(array).copy()
    free_array(array)
    return result

def read_serialized_array_pair_with_data_proprietorship(array) -> Tuple[int, np.ndarray, np.ndarray]:
    num, arr1, arr2 = read_serialized_array_pair(array)
    arr1, arr2 = arr1.copy(), arr2.copy()
    free_array(array)
    return num, arr1, arr2

def concatenate(l: List[np.ndarray], dtype=None):
    if dtype is not None:
        return np.concatenate(l + [np.zeros((0, ), dtype=np.int64)], dtype=dtype)
    return np.concatenate(l + [np.zeros((0, ), dtype=np.int64)])

class GameBuilder:
    def __init__(self, edge_index: np.ndarray,
                 num_pebbles: int,
                 num_nodes: Optional[int] = None):
        self.edge_index = edge_index
        self.num_nodes = maybe_num_nodes(edge_index, num_nodes)
        self.num_pebbles = num_pebbles
        self.edge_dict = to_edge_dict(edge_index, num_nodes) # keep this pointer alive
        self.builder = get_builder(npc.as_ctypes(self.edge_dict), 
                                   ctypes.c_long(num_pebbles),
                                   ctypes.c_long(self.num_nodes))
        self.initialize()

    def initialize(self) -> Optional[np.ndarray]:
        return read_serialized_array_with_data_proprietorship(
            initialize_states(self.builder)
        )

    def restrict(self, state_id: int,
                 pebble_id: int, 
                 new_node: int,
                 tag: int = 0,
                 record: bool = True,
                 mark_as_visited: bool = True) -> Optional[np.ndarray]:
        """
        If "record" is set to "True", will add an edge in the game
        state graph.

        If "mark_as_visited" is set to "True", will mark the state
        "state_id" as visited.
        """
        return read_serialized_array_with_data_proprietorship(
            restrict_from_state(self.builder, 
                                ctypes.c_long(state_id),
                                ctypes.c_long(pebble_id),
                                ctypes.c_long(new_node),
                                ctypes.c_long(tag),
                                ctypes.c_int(record),
                                ctypes.c_int(mark_as_visited))
        )
    
    def expand(self, state_id: int,
               pebble_id: int,
               tag: int = 0,
               record: bool = True,
               mark_as_visited: bool = True) -> Optional[int]:
        """
        If "record" is set to "True", will add an edge in the game
        state graph.

        If "mark_as_visited" is set to "True", will mark the state
        "state_id" as visited.
        """
        return int(
            expand_from_state(self.builder,
                                ctypes.c_long(state_id),
                                ctypes.c_long(pebble_id),
                                ctypes.c_long(tag),
                                ctypes.c_int(record),
                                ctypes.c_int(mark_as_visited))
        )
    
    def composite(self, state_id: int,
                  operation: List[Union[
                      Tuple[Literal['expand'], int],
                      Tuple[Literal['restrict'], int, int]
                  ]],
                  tag: int = 0,
                  record: bool = True,
                  mark_as_visited: bool = True) -> Optional[np.ndarray]:
        """
        Compose a few "expand" or "restrict" operations together as a
        single operation.

        The "operation" argument should specify the sequence of the
        individual operations, in the format
            - ('expand', pebble_id)
            - ('restrict', pebble_id, new_node)

        If "record" is set to "True", will add edges that represent
        the trace of the composite operation in the game state graph.

        If "mark_as_visited" is set to "True", will mark the state
        "state_id" as visited.
        """
        if operation == []:
            if mark_as_visited:
                self.mark_visited(state_id)
            return np.array([state_id, ], dtype=np.int64)

        last_op = operation[-1]
        if last_op[0] == 'expand':
            op_func = self.expand
            gather_func = np.array
        elif last_op[0] == 'restrict':
            op_func = self.restrict
            gather_func = concatenate
        args = last_op[1:]
        before_last: np.ndarray = self.composite(state_id,
                                                 operation[:-1],
                                                 tag=tag,
                                                 record=record,
                                                 mark_as_visited=mark_as_visited)
        return np.unique(gather_func(
            [op_func(state, *args, tag=tag, record=record, 
             mark_as_visited=False) for state in before_last], dtype=np.int64
        ))     
    
    def get_state(self, pebbled_nodes: np.ndarray, selected_cc: int, tag: int = 0) -> int:
        return int(get_state(self.builder, 
                             npc.as_ctypes(pebbled_nodes), 
                             ctypes.c_long(selected_cc),
                             ctypes.c_long(tag)))
            
    def serialize_state(self, state_id: int) -> Tuple[int, np.ndarray, np.ndarray]:
        return read_serialized_array_pair_with_data_proprietorship(
            display_state(self.builder, ctypes.c_long(state_id))
        )
    
    def is_spoiler_win(self, state_id: int) -> bool:
        return bool(
            spoiler_win(self.builder, ctypes.c_long(state_id))
        )
    
    def has_visited(self, state_id: int) -> bool:
        return bool(
            has_visited(self.builder, ctypes.c_long(state_id))
        )
    
    def game_graph_add_edge(self, start: int, end: int):
        add_edge(self.builder, ctypes.c_long(start), ctypes.c_long(end))
    
    def get_game_graph(self) -> np.ndarray:
        """
        In "edge_index" format.
        """
        return read_serialized_array_with_data_proprietorship(
            get_game_graph(self.builder)
        ).reshape(-1, 2).T
    
    def query_edge_cc(self, pebbled_nodes: np.ndarray) -> np.ndarray:
        return read_serialized_array_with_data_proprietorship(
            edge_to_cc_id(self.builder, npc.as_ctypes(pebbled_nodes))
        ).reshape(-1, 2).T
    
    def mark_visited(self, state_id: int):
        mark_visited(self.builder, ctypes.c_long(state_id))

    def __del__(self):
        if hasattr(self, 'builder') and self.builder is not None:
            free_builder(self.builder)
        
