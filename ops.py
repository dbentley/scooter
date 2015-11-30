from subprocess import Popen, PIPE
import tempfile
from scooter_types import *
from parser import *
import os

def update(e, n):
    if (n.op.type == 'setfile' and e.op.type == 'getfile'
        and e.op.args[0] not in n.op.args):
        return Edge(n.output, e.op, e.output)
    return None
    
def popen(inputs, op):
    args = op.args
    d = tempfile.mkdtemp(prefix='scooter')
    dirvalue = False
    if args[1:] and args[1] == '$@D':
        dirvalue = True
        output = os.path.join(d, 'output')
        os.mkdir(output)
        args = args[0:1] + args[2:]
    for (filename, contents) in zip(args[1:], inputs[1:]):
        f = open(d + '/' + filename, 'w')
        f.write(contents)
        f.close()
    o = Popen(args[0], cwd=d, shell=True, stdin=PIPE,
              stdout=PIPE).communicate(inputs[0])[0]
    if dirvalue:
        result, fs = [], []
        for triple in os.walk(output):
            d, _, filenames = triple
            for fname in filenames:
                full = os.path.join(d, fname)
                f = os.path.relpath(full, output)
                result.append(edit(0, append(open(full).read()), f))
                fs.append(f)
        result.append(Stmt([0] + fs, setfile(*fs), ["_"]))
        return result
    else:
        return [edit(0, append(o))]

def eval_op(inputs, op):
    args, type = op.args, op.type
    input, arg = (inputs or [None])[0], (op.args or [None])[0]
    if type == 'noop':
        return input()
    if type == 'append':
        return input() + arg
    if type == 'trim':
        return input()[arg:]
    if type == 'limit':
        return input()[:arg]
    if type == 'insert':
        before = input().ljust(arg)
        return before[:arg] + args[1] + before[arg:]
    if type == 'put':
        before = input().ljust(arg)
        return before[:arg] + args[1] + before[arg + len(args[1]):]
    if type == 'cat':
        return ''.join([i() for i in inputs])
    if type == 'setfile':
        return dict(zip(args, inputs[1:]) + (input() or {}).items())
    if type == 'getfile':
        return input()[arg]()

    raise NotImplementedError
