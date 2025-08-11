import gstaichi as ti

def bar(a, b):
    return a + b + 3

# diff

def entry(a: int, b: int):
    fn = bar
    return fn(a, b)

# diff
