import gstaichi as ti

# diff

def entry(a: int, b: int):
    for i, j in ti.static(ti.ndrange(2, 4)):
        pass

# diff
