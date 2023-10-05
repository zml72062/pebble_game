from count_drfwl2 import can_drfwl2_count, DRFWL1, DRFWL2, DRFWL3
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
    print(can_drfwl2_count(cycle(k), DRFWL1, 1))
    print(can_drfwl2_count(cycle(k), DRFWL2, 2))
    print(can_drfwl2_count(cycle(k), DRFWL3, 3))

for k in range(2, 8):
    print(f"{k}-path:")
    print(can_drfwl2_count(path(k), DRFWL1, 1))
    print(can_drfwl2_count(path(k), DRFWL2, 2))
    print(can_drfwl2_count(path(k), DRFWL3, 3))

