# -*- coding: utf-8 -*-
def permutations(iterable, r=None):
    # permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
    # permutations(range(3)) --> 012 021 102 120 201 210
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = range(n)
    cycles = range(n, n-r, -1)
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return

def product(*args, **kwds):
    # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
    # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

it = [
    'Aedes aegypti Definitely',
    'Aedes aegypti Probably',
    'Aedes albopictus Definitely',
    'Aedes albopictus Probably',
    'Aedes japonicus Definitely',
    'Aedes japonicus Probably',
    'Aedes koreicus Definitely',
    'Aedes koreicus Probably',
    'Unclassified',
    'Complex japonicus/koreicus',
    'Complex albopictus/cretinus',
    'Not sure',
    'Other species'
]

prod = product(it, repeat=3)

for p in prod:
    print(p)