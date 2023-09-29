# Determine the Substructure Counting Ability of Graph Algorithms via Pebble Games

This is a demo repo verifying the recently established equivalence between substructure counting ability of graph algorithms and the corresponding pebble games.

## Get Started

Start by compiling the C++ source
```
g++ -o cc_impl.so -fPIC -shared -std=c++11 cc_impl.cpp
```
This command works for Linux and MacOS systems.

## APIs

### Play the pebble game with GUI

To introduce the user with the rules of the pebble game, we provide a GUI for the pebble game.

In `game_gui.py`, there is a function `game_gui()`. Calling it with
```
game_gui(edge_index, num_pebbles, [num_nodes])
```
to launch a pebble game, where `num_nodes` is optional. Here `edge_index` follows the usual sparse adjacency matrix format as in PyTorch Geometric (PyG), and `num_pebbles` is the number of pebbles included in the game.

### Deciding substructure counting ability

As is recently established, a graph algorithm $A$ can **colorful** count a substructure $S$ if and only if Spoiler has a winning strategy in the pebble game corresponding to $A$ played on graph $S$. Moreover, $A$ can count a substructure $S$ if and only if it can colorful count all homomorphism images of $S$.

In `homo.py`, we provide a function `contract_all()` to compute all homomorphism images of a given graph. Calling it with
```
contract_all(edge_index, [num_nodes])
```
it will return a list of sparse adjacency matrices, representing all homomorphisms of the input graph.

In `game_search.py`, we provide a class `GameSearcher`, which searches the game graph of the pebble game by brute force, and return whether the algorithm corresponding to that pebble game can colorful count a substructure. Please see `count_fwl.py` and `count_localfwl2.py` for example usages.

## Tests

We provide two tests to verify the correctness of our implementation.

### Path and cycle counting power for $k$-FWL

In `test_fwl.py`, we verify that
* 1-WL can count 1- and 2-paths, but not other paths or any cycles.
* 2-FWL can count up to 6-paths and up to 7-cycles, but not longer paths or longer cycles.
* 3-FWL can count up to 8-paths and up to 8-cycles.

### Counting power of local FWL(2) variants

In `test_localfwl2.py`, we verify the modified versions of Lemmas F.18 ~ F.25 in the paper "A Complete Expressiveness Hierarchy for Subgraph GNNs via Subgraph Weisfeiler-Leman Tests". 
