#! /usr/bin/python

from collections import namedtuple
_lib = namedtuple('Lib', ['name', 'srcs', 'headers', 'deps'])
_test = namedtuple('Test', ['name', 'srcs', 'deps'])

build_text = open('BUILD').read()

libs, tests = {}, {}

def lib(*args):
    l = _lib(*args)
    libs[l.name] = l

def test(*args):
    t = _test(*args)
    tests[t.name] = t
  
exec(build_text)

plans = {}

def boilerplate():
    return (
"""
Stmt(["0"], getfile("BUILD"), ["buildtext"]),
Stmt(["0"], getfile("dunts.py"), ["duntstext"]),
Stmt([0, "duntstext", "buildtext"], func("chmod +x dunts.py && ./dunts.py", "$@D", "dunts.py", "BUILD"), ["plans"]),""")
        
def derive(val, name):
    return (
"""
Stmt(["plans"], getfile("%(val)s"), ["plan"]),
Stmt(["plan", "0"], recur(), ["%(name)s"]),"""
        % {'val': val, 'name': name})


def emit(plan_name, text):
    open('output/' + plan_name, 'w').write(text)

for l in libs:
    emit('build' + l, '')

for t in tests:
    emit('run' + t,
         '[' + boilerplate() + derive('build' + t, 'a.out') + """
Stmt([0, "a.out"], func('chmod +x a.out && ./a.out', 'a.out'), ['_']),
]""")
    test = tests[t]
    grab_srcs = ''.join(['Stmt(["0"], getfile("%(src)s"), ["%(src)s"]),\n' % {'src': s} for s in test.srcs])
    compile = """Stmt([0, %(srcs)s], func("gcc %(main)s && cat a.out", %(srcs)s), ["_"]),
""" % { 'srcs': ', '.join(['"%s"' % s for s in test.srcs]), 'main': test.srcs[0]}
    emit('build' + t,
         '[' + boilerplate() + '\n' + grab_srcs + compile
         + ']')

emit('all', '[ ' + boilerplate() + ''.join([derive('run' + t, 'run' + t) for t in tests.keys()]) + (
"""
Stmt(["%s"], cat() ,['_'],)
]""" % ', '.join(['run' + t for t in tests.keys()])))

for k in plans:
    print '%s = %s' % (k, plans[k])
