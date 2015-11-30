from scooter_types import *
from parser import parse
from ops import popen, eval_op, update

states, edges = [State(0)], []

def q(program):
    result = run(program)
    return Result(result.id, eval(result))

def run(stmts, ctx=None):
    ctx, result = ctx or {}, states[0]
    for s in stmts:
        input = [ctx.get(i) or states[i] for i in s.inbind]
        result = ctx[s.outbind[0]] = apply(s.op, input)
    return result
    
def apply(op, input):
    if op.type == 'recur':
        return run(parse(eval(input[0])),
                   dict((str(i), j) for i, j in enumerate(input[1:])))
    for e in edges:
        if e.input == input and e.op == op and op.type != 'proc':
            return e.output[0]
    s = State(len(states))
    states.append(s)
    n = Edge(input, op, [s])
    edges.extend([n] + [update(e, n) for e in edges if update(e, n)])
    return s

def eval(s):
    if s is states[0]: return ''
    return eval_edge([e for e in edges if s in e.output][-1])

def eval_edge(e):
    if e.op.type in ['proc', 'func']:
        e = Edge([run(popen([eval(s) for s in e.input], e.op))],
                 Op('noop', []), e.output)
        edges.append(e)
    return eval_op([lambda s=s: eval(s) for s in e.input], e.op)
