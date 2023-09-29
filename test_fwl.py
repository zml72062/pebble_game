from count_fwl import can_kfwl_count
import numpy as np

def cycle(k):
    return np.concatenate(
        [np.array([[i, i+1],
                   [i+1, i]], dtype=np.int64) for i in range(k-1)
        ] + [np.array([[k-1, 0],
                       [0, k-1]], dtype=np.int64)], axis=1)

def path(k):
    return np.concatenate(
        [np.array([[i, i+1],
                   [i+1, i]], dtype=np.int64) for i in range(k)
        ], axis=1)

for k in range(3, 9):
    print(f"{k}-cycle:")
    print(can_kfwl_count(cycle(k), 1)) # 1-WL
    print(can_kfwl_count(cycle(k), 2)) # 2-FWL
    print(can_kfwl_count(cycle(k), 3)) # 3-FWL

for k in range(1, 9):
    print(f"{k}-path:")
    print(can_kfwl_count(path(k), 1)) # 1-WL
    print(can_kfwl_count(path(k), 2)) # 2-FWL
    print(can_kfwl_count(path(k), 3)) # 3-FWL
