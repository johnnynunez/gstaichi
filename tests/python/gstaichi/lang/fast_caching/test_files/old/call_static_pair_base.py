import gstaichi as ti

# random text adsfas dfa a ag reg rg 

def bar(a, b):
    return a + b

def foo(a, b):
    bar(a, b)
    bar2, a2 = ti.static(bar, a)
    return bar2(a2, b)

def entry(a: int, b: int):
    return foo(a, b)

# random text ggrgrht,thth
