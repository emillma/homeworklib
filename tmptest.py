import numpy as np
from time import perf_counter
from functools import lru_cache


@lru_cache(maxsize=100)
def getidx(n, space):
    step = 1 << (n//space).bit_length()
    if n < space:
        return n
    elif n % step != 0:
        return None
    number = n//step - (space+1)//2
    replacing = step//2 + number*step
    return getidx(replacing, space)


space = 14
data = list(range(space))
arg = space
step = 1

N = 2000000
t0 = perf_counter() 
for n in range(space, N):
    if np.all([i % step == 0 for i in data]):
        step *= 2
    if n % step != 0:
        continue
    test = [int(i % step == 0) for i in data]
    keydir = [(t, v) for (t, v) in zip(test, data)]
    arg = min(range(len(data)), key=lambda i: keydir[i])
    data[arg] = n
d0 = perf_counter()-t0

t0 = perf_counter()
data2 = list(range(space))
for n in range(space, N):
    if idx := getidx(n, space):
        data2[idx] = n
d1 = perf_counter()-t0
print(d0, d1)


pass
