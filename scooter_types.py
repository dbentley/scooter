from collections import namedtuple
Statement = namedtuple('Statement', ['inbind', 'op', 'outbind'])
Edge = namedtuple('Edge', ['input', 'op', 'output'])
State = namedtuple('State', ['id'])
Result = namedtuple('Result', ['id', 'contents'])
Op = namedtuple('Op', ['type', 'args'])

