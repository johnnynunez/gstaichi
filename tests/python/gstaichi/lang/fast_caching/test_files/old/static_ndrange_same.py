import gstaichi as ti

# same

def entry(a: int, b: int):
    for i, j in ti.static(ti.ndrange(2, 3)):
        pass

# same
