import gstaichi as ti

def bar(a, b):
    return a + b

# same

def entry(a: int, b: int):
    fn = bar
    return fn(a, b)

# same
