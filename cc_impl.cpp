#include <set>
#include <map>
#include <vector>
#include <cstdlib>
#include <cstdio>

using EdgeSet = std::set<long>;
using std::vector;

void add_two_dir(EdgeSet& edge_set, long start, long end, long num_nodes)
{
    edge_set.insert(start * num_nodes + end);
    edge_set.insert(end * num_nodes + start);
}

void rm_two_dir(long* edge_set, long start, long end, long num_nodes)
{
    edge_set[start * num_nodes + end] = -1;
    edge_set[end * num_nodes + start] = -1;
}

int is_pebbled(const long* pebbled_nodes, long node, long num_pebbles)
{
    for (long i = 0; i < num_pebbles; i++)
    {
        if (node == pebbled_nodes[i])
            return 1;
    }
    return 0;
}

void find_cc(long* edge_set, /* WILL modify "edge_set"! */
             const long* pebbled_nodes,
             EdgeSet& output, /* EMPTY at the beginning */
             long start, long end, long num_nodes, long num_pebbles)
{
    add_two_dir(output, start, end, num_nodes);
    rm_two_dir(edge_set, start, end, num_nodes);
    int contain_start = is_pebbled(pebbled_nodes, start, num_pebbles),
        contain_end = is_pebbled(pebbled_nodes, end, num_pebbles);
    if (!contain_end)
    {
        long* partial = edge_set + end * num_nodes;
        for (long i = 0; i < num_nodes; i++)
            if (partial[i] != -1) 
                find_cc(edge_set, pebbled_nodes, output, i, end, num_nodes, num_pebbles);
    }
    if (!contain_start)
    {
        long* partial = edge_set + start * num_nodes;
        for (long i = 0; i < num_nodes; i++)
            if (partial[i] != -1) 
                find_cc(edge_set, pebbled_nodes, output, i, start, num_nodes, num_pebbles);
    }
}

vector<EdgeSet> find_all_cc(long* edge_set,
                            const long* pebbled_nodes,
                            long num_nodes, long num_pebbles)
{
    vector<EdgeSet> all_cc;
    long edge_set_len = num_nodes * num_nodes;
    for (long i = 0; i < edge_set_len; i++)
        if (edge_set[i] != -1) {
            EdgeSet next_set;
            long start = i / num_nodes, end = i % num_nodes;
            find_cc(edge_set, pebbled_nodes, next_set, start, end, num_nodes, num_pebbles);
            all_cc.push_back(next_set);
        }
    return all_cc;
}

void keep_only_current(long* edge_set, const EdgeSet& current, long num_nodes)
{
    long len_edge_set = num_nodes * num_nodes;
    for (long i = 0; i < len_edge_set; i++) {
        if (current.find(i) == current.end()) {
            edge_set[i] = -1;
        }
    }
}

vector<EdgeSet> restrict_cc(long* edge_set,
                            const EdgeSet& current,
                            const long* pebbled_nodes,
                            long num_nodes, long num_pebbles)
{
    keep_only_current(edge_set, current, num_nodes);
    return find_all_cc(edge_set, pebbled_nodes, num_nodes, num_pebbles);
}

EdgeSet expand_cc(long* edge_set,
                  const EdgeSet& current,
                  const long* pebbled_nodes,
                  long num_nodes, long num_pebbles)
{
    EdgeSet expanded_set;
    if (current.empty())
        return expanded_set;
    long first = *current.begin();
    find_cc(edge_set, pebbled_nodes, expanded_set, first / num_nodes,
            first % num_nodes, num_nodes, num_pebbles);
    return expanded_set;
}

long* copy(const long* edge_set, long num_nodes) {
    long* copied = (long*)malloc(num_nodes * num_nodes * sizeof(long));
    if (copied)
        memcpy(copied, edge_set, num_nodes * num_nodes * sizeof(long));
    return copied;
}

/* This is a helper function. */
long* to_edge_dict(long* edge_index, long num_nodes, long num_edges) {
    long* copied = (long*)malloc(num_nodes * num_nodes * sizeof(long));
    if (copied) {
        memset(copied, -1, num_nodes * num_nodes * sizeof(long));
        for (long i = 0; i < num_edges; i++) {
            copied[edge_index[i] * num_nodes + edge_index[i + num_edges]] = i;
        }
    }
    return copied;
}

struct SetIndCache {
private:
    const long* edge_set;
    long num_pebbles;
    long num_nodes;
    /* 
        Store "pebble configuration" -> "index -> connected component"
    */
    std::map<std::set<long>, std::vector<EdgeSet>> cache_ind2set;

public:
    SetIndCache(const long* _edge_set, long _num_pebbles, long _num_nodes):
    edge_set(_edge_set), num_pebbles(_num_pebbles), num_nodes(_num_nodes) {}
    
    /* Singleton */
    SetIndCache(const SetIndCache& _cache) = delete;
    SetIndCache(SetIndCache&& _cache) = delete;
    SetIndCache& operator=(const SetIndCache& _cache) = delete;
    SetIndCache& operator=(SetIndCache&& _cache) = delete;
    ~SetIndCache() = default;

    const EdgeSet& ind2set(const long* pebbled_nodes,
                           long ind) {
        add_cc(pebbled_nodes);
        std::set<long> pebbs(pebbled_nodes, pebbled_nodes + num_pebbles);
        return cache_ind2set.find(pebbs)->second[ind];
    }

    long set2ind(const long* pebbled_nodes,
                 const EdgeSet& in_set) {
        add_cc(pebbled_nodes);
        std::set<long> pebbs(pebbled_nodes, pebbled_nodes + num_pebbles);
        const auto& vec = cache_ind2set.find(pebbs)->second;
        auto veclen = vec.size();
        for (long i = 0; i < veclen; i++) {
            if (vec[i] == in_set) {
                return i;
            }
        }
        return -1;
    }

    long add_cc(const long* pebbled_nodes) {
        std::set<long> pebbs(pebbled_nodes, pebbled_nodes + num_pebbles);
        auto ind2set_val = cache_ind2set.find(pebbs);

        if (ind2set_val == cache_ind2set.end()) {
            long* copy_edge_set = copy(edge_set, num_nodes);
            auto all_cc = find_all_cc(copy_edge_set, pebbled_nodes, num_nodes, num_pebbles);
            cache_ind2set[pebbs] = all_cc;
            free(copy_edge_set);
        }
        return cache_ind2set[pebbs].size();
    }

    std::map<long, long> edge_to_cc_id(const long* pebbled_nodes) {
        add_cc(pebbled_nodes);
        std::set<long> pebbs(pebbled_nodes, pebbled_nodes + num_pebbles);
        const auto& vec = cache_ind2set[pebbs];
        auto veclen = vec.size();
        std::map<long, long> output;
        for (long i = 0; i < veclen; i++) {
            for (auto& edge: vec[i]) {
                output[edge] = i;
            }
        }
        return output;
    }
};

struct GameBuilder {
private:
    const long* edge_set;
    long num_pebbles;
    long num_nodes;

public:
    SetIndCache* cache; /* Must be "new"ed! */

private:    
    /* Two caches:
          - "state_dict": maps <pebbled_nodes, cc_id> to state id
          - "state_vec": maps state id to <pebbled_nodes, cc_id>
    */
    std::map<std::pair<long, std::pair<std::vector<long>, long>>, long> state_dict;
    std::vector<std::pair<long, std::pair<std::vector<long>, long>>> state_vec;

public:
    std::vector<int> visited; /* Whether a state is visited when constructing
                                 the graph */
    std::set<std::pair<long, long>> game_graph;

    GameBuilder(const long* _edge_set, long _num_pebbles, long _num_nodes,
                SetIndCache& _cache):
    edge_set(_edge_set), num_pebbles(_num_pebbles), num_nodes(_num_nodes),
    cache(&_cache) {}

    /* Singleton */
    GameBuilder(const GameBuilder& _builder) = delete;
    GameBuilder(GameBuilder&& _builder) = delete;
    GameBuilder& operator=(const GameBuilder& _builder) = delete;
    GameBuilder& operator=(GameBuilder&& _builder) = delete;
    ~GameBuilder() {
        delete cache; /* "cache" must be previously "new"ed! */
    }

public:
    /* Return the state id. */
    long add_state(const long* pebbled_nodes, long selected_cc, long tag) {
        std::vector<long> to_vec(pebbled_nodes, pebbled_nodes + num_pebbles);
        auto key = std::make_pair(tag, std::make_pair(to_vec, selected_cc));
        if (state_dict.find(key) == state_dict.end()) {
            state_vec.push_back(key);
            state_dict[key] = state_vec.size() - 1;
            visited.push_back(0);
        }
        return state_dict[key];
    }

    void add_edge(long from, long to) {
        game_graph.insert({from, to});
    }

    std::pair<long, std::pair<const vector<long>&, const EdgeSet&>> display_state(long id) {
        return {state_vec[id].first,
                {state_vec[id].second.first, 
                 cache->ind2set(state_vec[id].second.first.data(), state_vec[id].second.second)}};
    }

    int spoiler_win(long id) {
        return cache->ind2set(state_vec[id].second.first.data(), state_vec[id].second.second).size() <= 2;
    }

    vector<long> initialize_states() {
        vector<long> pebbled_nodes(num_pebbles, -1);
        long init_num_cc = cache->add_cc(pebbled_nodes.data());
        vector<long> added_states;
        for (long i = 0; i < init_num_cc; i++) 
            added_states.push_back(add_state(pebbled_nodes.data(), i, 0));
        
        return added_states;
    }

    /*
        From the given state, place a new pebble (with index "pebble_id")
        at "new_node", then return the vector of all generated states.
    */
    vector<long> restrict_from_state_id(long state_id, long pebble_id, long new_node, long tag, int record, int mark_as_visited) {
        if (mark_as_visited)
            visited[state_id] = 1;
        long* copy_edge_set = copy(edge_set, num_nodes);
        auto state = state_vec[state_id];

        EdgeSet old_copy(cache->ind2set(state.second.first.data(), state.second.second));
        
        std::vector<long> new_pebble_config(state.second.first.begin(), state.second.first.end());
        if (new_pebble_config[pebble_id] != -1)
            fprintf(stderr, "Warning: Try to move (instead of adding) a pebble.\n");

        new_pebble_config[pebble_id] = new_node;

        auto restricted = restrict_cc(copy_edge_set, old_copy, 
                                      new_pebble_config.data(), 
                                      num_nodes, num_pebbles);
        std::vector<long> all;
        for (auto& s: restricted) {
            auto result = add_state(new_pebble_config.data(), cache->set2ind(new_pebble_config.data(), s), tag);
            all.push_back(result);
            if (record)
                add_edge(state_id, result);
        }
        free(copy_edge_set);
        return all;
    }

    /*
        From the given state, remove the pebble with index "pebble_id",
        then return the generated state.
    */
    long expand_from_state_id(long state_id, long pebble_id, long tag, int record, int mark_as_visited) {
        if (mark_as_visited)
            visited[state_id] = 1;
        long* copy_edge_set = copy(edge_set, num_nodes);
        auto state = state_vec[state_id];

        EdgeSet old_copy(cache->ind2set(state.second.first.data(), state.second.second));
        
        std::vector<long> new_pebble_config(state.second.first.begin(), state.second.first.end());
        if (new_pebble_config[pebble_id] == -1)
            fprintf(stderr, "Warning: Try to remove an absent pebble.\n");

        new_pebble_config[pebble_id] = -1;

        auto expanded = expand_cc(copy_edge_set, old_copy,
                                  new_pebble_config.data(),
                                  num_nodes, num_pebbles);
        
        auto result = add_state(new_pebble_config.data(), cache->set2ind(new_pebble_config.data(), expanded), tag);
        if (record)
            add_edge(state_id, result);

        free(copy_edge_set);
        return result;
    }

    void mark_visited(long state_id) {
        visited[state_id] = 1;
    }
};

/* The 0-th element of the array indicates the length. 
   The other elements are the content of the array. */
long* serialize_vector(const std::vector<long>& vec) {
    long* serialize = (long*)malloc(sizeof(long) * (vec.size() + 1));
    serialize[0] = vec.size();
    memcpy(serialize + 1, vec.data(), vec.size() * sizeof(long));
    return serialize;
}

/* The 0-th element of the array is the number.
   The 1-st element of the array is the length of the vector.
   The 2-nd element of the array is the length of the container.
   The other elements are the content of the vector and the container,
   put sequentially. */
template <class T>
long* serialize_vector_and_container(long number,
                                     const std::vector<long>& vec,
                                     const T& container) {
    long* serialize = (long*)malloc(sizeof(long) * (vec.size() + container.size() + 3));
    std::vector<long> container_to_vec(container.begin(), container.end());
    serialize[0] = number;
    serialize[1] = vec.size();
    serialize[2] = container.size();
    memcpy(serialize + 3, vec.data(), vec.size() * sizeof(long));
    memcpy(serialize + 3 + vec.size(), container_to_vec.data(), container.size() * sizeof(long));
    return serialize;
}

/* C interfaces for binding with Python. */
extern "C" {
    void* get_builder(long* edge_set, long num_pebbles, long num_nodes) {
        SetIndCache* cache = new SetIndCache(edge_set, num_pebbles, num_nodes);
        GameBuilder* builder = new GameBuilder(edge_set, num_pebbles, num_nodes, *cache);
        return builder;
    }

    void free_builder(void* builder) {
        delete (GameBuilder*)builder;
    }

    long* initialize_states(void* builder) {
        return serialize_vector(((GameBuilder*)builder)->initialize_states());
    }

    long* restrict_from_state(void* builder, long state_id, long pebble_id, long new_node, long tag, int record, int mark_as_visited) {
        return serialize_vector(((GameBuilder*)builder)->restrict_from_state_id(state_id, pebble_id, new_node, tag, record, mark_as_visited));
    }

    long expand_from_state(void* builder, long state_id, long pebble_id, long tag, int record, int mark_as_visited) {
        return ((GameBuilder*)builder)->expand_from_state_id(state_id, pebble_id, tag, record, mark_as_visited);
    }

    void mark_visited(void* builder, long state_id) {
        ((GameBuilder*)builder)->mark_visited(state_id);
    }

    long* display_state(void* builder, long id) {
        auto display = ((GameBuilder*)builder)->display_state(id);
        return serialize_vector_and_container(display.first, display.second.first, display.second.second);
    }

    int spoiler_win(void* builder, long id) {
        return ((GameBuilder*)builder)->spoiler_win(id);
    }

    int has_visited(void* builder, long id) {
        return ((GameBuilder*)builder)->visited[id];
    }

    long* get_game_graph(void* builder) {
        auto graph = ((GameBuilder*)builder)->game_graph;
        long length = graph.size() * 2;
        long* serialize = (long*)malloc(sizeof(long) * (length + 1));
        serialize[0] = length;
        serialize += 1;
        for (auto& pair: graph) {
            *serialize = pair.first;
            *(serialize + 1) = pair.second;
            serialize += 2;
        }
        return serialize - length - 1;
    }

    long* edge_to_cc_id(void* builder, long* pebbled_nodes) {
        auto graph = ((GameBuilder*)builder)->cache->edge_to_cc_id(pebbled_nodes);
        long length = graph.size() * 2;
        long* serialize = (long*)malloc(sizeof(long) * (length + 1));
        serialize[0] = length;
        serialize += 1;
        for (auto& pair: graph) {
            *serialize = pair.first;
            *(serialize + 1) = pair.second;
            serialize += 2;
        }
        return serialize - length - 1;
    }

    long get_state(void* builder, long* pebbled_nodes, long selected_cc, long tag) {
        return ((GameBuilder*)builder)->add_state(pebbled_nodes, selected_cc, tag);
    }

    void add_edge(void* builder, long start, long end) {
        ((GameBuilder*)builder)->add_edge(start, end);
    }

    void free_array(long* array) {
        free(array);
    }

    /* Helper function for pointer arithmetics in Python. */
    long* ptr_add(long* ptr, long offset) {
        return ptr + offset;
    }
}
