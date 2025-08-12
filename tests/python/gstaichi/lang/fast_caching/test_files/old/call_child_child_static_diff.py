import gstaichi as ti

# random text adsfas dfa a ag reg rg 

def bar(a, b):
    return a + b + 3

def foo(a, b):
    return ti.static(bar)(a, b)

def entry(a: int, b: int):
    return foo(a, b)

# random text ggrgrht,thth
