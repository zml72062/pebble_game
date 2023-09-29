import tkinter as tk
from tkinter.font import Font
import numpy as np
from typing import Optional, List, Tuple, Dict, Literal
from cc import GameBuilder, maybe_num_nodes
import math

"""
Util functions.
"""
def keep_one_dir(edge_index: np.ndarray) -> np.ndarray:
    return edge_index[:, edge_index[0] < edge_index[1]]

def accurate_coord(coord_i: Tuple[float, float],
                   coord_j: Tuple[float, float],
                   radius: float = 0.0) -> Tuple[float, float, float, float]:
    i_x, i_y = coord_i
    j_x, j_y = coord_j
    distance = ((i_x - j_x) ** 2 + (i_y - j_y) ** 2) ** 0.5
    cos, sin = (i_x - j_x) / distance, (i_y - j_y) / distance
    return i_x - radius * cos, i_y - radius * sin, j_x + radius * cos, j_y + radius * sin

def generate_color(i: int) -> int:
    colors = [0xff0000,
              0x00ff00,
              0x0000ff,
              0xffff00,
              0xff00ff,
              0x00ffff]
    color_type = i % 6
    darkness = (i // 6 + 1) * 2 / 3
    return (0x10101 * min(0xff, int(0xff / darkness))) & colors[color_type]

def dict_index(_dict: Dict[int, np.ndarray], number):
    for (key, value) in _dict.items():
        if number in value:
            return key
    return -1

"""
Handle game operations.
"""
def handle_move_on_node(canvas, obj):
    def handle(event):
        x0, y0, x1, y1 = canvas.coords(obj)
        canvas.coords(obj, x0-3, y0-3, x1+3, y1+3)
    return handle

def handle_move_off_node(canvas, obj):
    def handle(event):
        x0, y0, x1, y1 = canvas.coords(obj)
        canvas.coords(obj, x0+3, y0+3, x1-3, y1-3)
    return handle

def handle_click_pebble(canvas, obj, app: 'Application'):
    def handle(event):
        if app.turn == 'Spoiler': # only respond at Spoiler turn
            _, ind, _ = canvas.itemcget(obj, 'tags').split('_')
            color = canvas.itemcget(obj, 'fill')
            ind = int(ind)
            if color == 'gray': # remove a pebble from the graph
                app.spoiler_move.action = 'expand'
                app.spoiler_move.pebble_id = ind
                node = app.pebbles[ind]
                canvas.itemconfig(obj, fill=app.pebble_colors[ind],
                                  outline=app.pebble_colors[ind])
                app.pebbles[ind] = -1
                try:
                    color_node = app.pebble_colors[list(app.pebbles).index(node)]
                except ValueError:
                    color_node = 'gray'
                canvas.itemconfig(app.node_ovals[node], fill=color_node, outline=color_node)
                state = app.builder.expand(app.game_state, ind)
                app.candidate_cc = {state: app.builder.serialize_state(state)[2]}
                app.generate_cc()
                app.turn = 'Duplicator'
                app.draw_title()
            else:
                app.spoiler_move.action = 'restrict'
                app.spoiler_move.pebble_id = ind
                canvas.itemconfig(obj, fill='gray',
                                  outline='gray')
                app.turn = f'Restrict_{ind}_'
    return handle

def handle_click_node(canvas, obj, app: 'Application'):
    def handle(event):
        if app.turn.startswith('Restrict'):
            _, ind, _ = app.turn.split('_')
            _, node, _ = canvas.itemcget(obj, 'tags').split('_')
            node, ind = int(node), int(ind)
            app.spoiler_move.pebbled_node = node
            app.pebbles[ind] = node
            try:
                color_node = app.pebble_colors[list(app.pebbles).index(node)]
            except ValueError:
                color_node = 'gray'
            canvas.itemconfig(app.node_ovals[node], fill=color_node, outline=color_node)
            out_states = app.builder.restrict(app.game_state,
                                              app.spoiler_move.pebble_id, node)
            app.candidate_cc = {
                state: app.builder.serialize_state(state)[2] for state in out_states
            }
            app.generate_cc()
            app.turn = 'Duplicator'
            app.draw_title()
    return handle

def handle_click_edge(canvas, obj, app: 'Application'):
    def handle(event):
        if app.turn == 'Duplicator':
            _, i, j, _ = canvas.itemcget(obj, 'tags').split('_')
            i, j = int(i), int(j)
            chosen_state = dict_index(app.candidate_cc, i * app.num_nodes + j)
            if chosen_state != -1:
                app.selected_edges = app.cc_list[app.cc_map[(i, j)]]
                app.game_state = chosen_state
                for (i_, j_) in app.edges:
                    canvas.itemconfig(app.edge_lines[(i_, j_)], 
                                      fill='orange' if (i_, j_) in app.selected_edges
                                           else 'black')
                app.turn = 'Spoiler'
                app.draw_title()
                if app.builder.is_spoiler_win(app.game_state):
                    info = tk.Toplevel(app.master)
                    info.title('Game Over')
                    info.geometry('200x80')
                    info.resizable(False, False)
                    tk.Label(info, text='Spoiler wins!').pack(anchor=tk.CENTER)
    return handle
            
def handle_move_on_edge(canvas, obj, app: 'Application'):
    def handle(event):
        _, i, j, _ = canvas.itemcget(obj, 'tags').split('_')
        i, j = int(i), int(j)
        for (i_, j_) in app.cc_list[app.cc_map[(i, j)]]:
            canvas.itemconfig(app.edge_lines[(i_, j_)], width=4, fill='red')
    return handle

def handle_move_off_edge(canvas, obj, app: 'Application'):
    def handle(event):
        _, i, j, _ = canvas.itemcget(obj, 'tags').split('_')
        i, j = int(i), int(j)
        for (i_, j_) in app.cc_list[app.cc_map[(i, j)]]:
            canvas.itemconfig(app.edge_lines[(i_, j_)], width=2, 
                              fill='black' if (i_, j_) not in app.selected_edges
                                    else 'orange')
    return handle

class SpoilerMove:
    action: Literal['restrict', 'expand']
    pebble_id: int
    pebbled_node: int

class Application:
    def __init__(self, master,
                 edge_index: np.ndarray,
                 num_pebbles: int,
                 num_nodes: Optional[int] = None):
        self.master = master
        self.num_nodes = maybe_num_nodes(edge_index, num_nodes)
        self.edges = keep_one_dir(edge_index).T
        self.num_pebbles = num_pebbles
        self.pebbles = np.full((num_pebbles, ), -1, dtype=np.int64)
        self.builder = GameBuilder(edge_index, num_pebbles, num_nodes)
        self.game_state = 0
        self.turn = 'Duplicator'
        self.selected_edges: List[int] = []
        out_states = self.builder.initialize()
        self.candidate_cc = {
            state: self.builder.serialize_state(state)[2] for state in out_states
        }
        self.spoiler_move = SpoilerMove()
        self.create_graph()
        self.generate_cc()
        self.draw_title()
        for i in range(self.num_pebbles):
            self.canvas.tag_bind(f'pebble_{i}_', 
                                 '<Enter>',
                                 handle_move_on_node(self.canvas,
                                                     self.pebble_ovals[i]))
            self.canvas.tag_bind(f'pebble_{i}_', 
                                 '<Leave>',
                                 handle_move_off_node(self.canvas,
                                                      self.pebble_ovals[i]))
            self.canvas.tag_bind(f'pebble_{i}_', 
                                 '<Button-1>',
                                 handle_click_pebble(self.canvas,
                                                     self.pebble_ovals[i],
                                                     self))
            self.canvas.tag_bind(f'pebble_{i}_', 
                                 '<Double-Button-1>',
                                 handle_click_pebble(self.canvas,
                                                     self.pebble_ovals[i],
                                                     self))
            
        for i in range(self.num_nodes):
            self.canvas.tag_bind(f'node_{i}_', 
                                 '<Enter>',
                                 handle_move_on_node(self.canvas,
                                                     self.node_ovals[i]))
            self.canvas.tag_bind(f'node_{i}_', 
                                 '<Leave>',
                                 handle_move_off_node(self.canvas,
                                                      self.node_ovals[i]))
            self.canvas.tag_bind(f'node_{i}_', 
                                 '<Button-1>',
                                 handle_click_node(self.canvas,
                                                   self.node_ovals[i],
                                                   self))
            self.canvas.tag_bind(f'node_{i}_', 
                                 '<Double-Button-1>',
                                 handle_click_node(self.canvas,
                                                   self.node_ovals[i],
                                                   self))

        for (i, j) in self.edges:
            self.canvas.tag_bind(f'edge_{i}_{j}_',
                                 '<Enter>',
                                 handle_move_on_edge(self.canvas,
                                                     self.edge_lines[(i, j)],
                                                     self))
            self.canvas.tag_bind(f'edge_{i}_{j}_',
                                 '<Leave>',
                                 handle_move_off_edge(self.canvas,
                                                      self.edge_lines[(i, j)],
                                                      self))
            self.canvas.tag_bind(f'edge_{i}_{j}_',
                                 '<Button-1>',
                                 handle_click_edge(self.canvas,
                                                   self.edge_lines[(i, j)],
                                                   self))
            self.canvas.tag_bind(f'edge_{i}_{j}_',
                                 '<Double-Button-1>',
                                 handle_click_edge(self.canvas,
                                                   self.edge_lines[(i, j)],
                                                   self))
        
    def generate_cc(self):
        edge_id, cc_id = self.builder.query_edge_cc(self.pebbles)
        row, col = edge_id // self.num_nodes, edge_id % self.num_nodes
        row, col, cc_id = row[row < col], col[row < col], cc_id[row < col]
        self.cc_map = {(i, j): cc for (i, j, cc) in zip(row, col, cc_id)}
        self.cc_list = [[] for _ in range(cc_id.max() + 1)]
        for (i, j, cc) in zip(row, col, cc_id):
            self.cc_list[cc].append((i, j))

    def next_player(self):
        if self.turn == 'Spoiler' or self.turn.startswith('Restrict'):
            return 'Spoiler', 'red'
        else:
            return 'Duplicator', 'blue'

    def create_graph(self):
        self.canvas = tk.Canvas(self.master, 
                                width=800, height=600, 
                                bg='white')
        self.canvas.pack(anchor=tk.CENTER, expand=True)

        ### Draw nodes
        center_x, center_y = 250.0, 350.0
        radius = 200.0
        min_angle = 2 * math.pi / self.num_nodes
        self.node_coords: List[Tuple[float, float]] = []
        self.node_ovals: List[int] = []
        self.node_text: List[int] = []
        for i in range(self.num_nodes):
            center_i_x = center_x + radius * math.cos(i * min_angle)
            center_i_y = center_y - radius * math.sin(i * min_angle)
            self.node_coords.append((center_i_x, center_i_y))
            self.node_ovals.append(
                self.canvas.create_oval(center_i_x - 7, center_i_y - 7,
                                        center_i_x + 7, center_i_y + 7,
                                        fill='gray', outline='gray', 
                                        tags=f'node_{i}_')
            )
            self.node_text.append(
                self.canvas.create_text(center_x + (radius + 17) * math.cos(i * min_angle),
                                        center_y - (radius + 17) * math.sin(i * min_angle),
                                        text=f'{i}', tags=f'node_text_{i}')
            )
            
        ### Draw edges
        self.edge_lines: Dict[Tuple[int, int], int] = {}
        for (i, j) in self.edges:
            # Calculate accurate start/end point
            self.edge_lines[(i, j)] = self.canvas.create_line(
                    *accurate_coord(self.node_coords[i], self.node_coords[j], 7), 
                    width=2, fill='black', tags=f'edge_{i}_{j}_'
            )
            
        ### Draw pebbles
        center_x, y_min, y_inter = 650.0, 250.0, 250.0 / self.num_pebbles
        self.pebble_ovals: List[int] = []
        self.pebble_colors: List[str] = []
        for i in range(self.num_pebbles):
            center_y = y_min + y_inter * i
            self.pebble_colors.append(f'#{"%06x" % generate_color(i)}')
            self.pebble_ovals.append(self.canvas.create_oval(
                center_x - 7, center_y - 7,
                center_x + 7, center_y + 7,
                fill=self.pebble_colors[i], 
                outline=self.pebble_colors[i], 
                tags=f'pebble_{i}_'
            ))

        player_name, player_color = self.next_player()
        self.title = self.canvas.create_text(400, 50, 
                                             text=f"{player_name}'s turn",
                                             fill=player_color,
                                             font=Font(self.canvas, size=30))

    def draw_title(self):
        player_name, player_color = self.next_player()
        self.canvas.itemconfig(self.title, text=f"{player_name}'s turn",
                               fill=player_color)
        
def game_gui(edge_index: np.ndarray, 
             num_pebbles: int, 
             num_nodes: Optional[int] = None):
    window = tk.Tk()
    window.geometry('800x600')
    window.title('Pebble Game')
    window.minsize(800, 600)

    Application(window, edge_index, num_pebbles, num_nodes)
    window.mainloop()
