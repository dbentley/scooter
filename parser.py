import scooter_types
import scooter

for o in ['noop', 'append', 'trim', 'limit', 'insert', 'put', 'proc', 'func', 'cat', 'setfile', 'getfile', 'recur']:
    locals()[o] = (lambda n: lambda *args: scooter_types.Op(n, args))(o)
    
def edit(before, op, after='_'):
    return scooter_types.Statement([before], op, [after])

Stmt = scooter_types.Statement
Op = scooter_types.Op

def parse(text):
    return eval(text)
