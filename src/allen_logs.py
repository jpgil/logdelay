from random import *
from statistics import *
import networkx as nx

class AllenLog():
    L_serials=['12356', '12456', '12476']
    L_loops  =['452', '524', '523', '53', '7']
    
    def __init__(self, path_length=3, N=10, loop_repeats=4, alphabet=None):
        """
        N           : number of traces
        loop_repeats: repetitions of each loop
        """
        self.N = N
        self.loop_repeats = loop_repeats
        self.path_length = path_length
        
        mapping = { str(i): alphabet.next(path_length) for i in [1,2,3,4,5,6,7] }
        
        self.symbols = sorted([ s for t in mapping.items() for s in t[1] ])
        if len(self.symbols) != len(set(self.symbols)):
            raise ValueError("symbols in mapping must be unique")
        
        self.mapping = { key: list(value) for key, value in mapping.items() }
        L = self.L_serials + self.L_loops
        
        self.graph = nx.DiGraph()
        for T in L:
            for u, v in zip(T[:-1], T[1:]):
                self.graph.add_edge(u, v)
                
        # Strategy: generate once, then just read
        self.generate()
        
    @property
    def log(self):
        return self.generated_log
        
    @property
    def mapped_log(self):
        A = []
        for T in self.log:
            A.append( [ x for s in T for x in self.mapping[s] ] )
        return A
    
    @property
    def paths(self):
        return list(self.mapping.values())

    @property
    def stats(self):
        s = { 'log':{}, 'allen trace': {}, 'mapped trace': {}, 'symbol': {} }
        s['log']['length'] = len(self.log)
        s['log']['loop_repeats'] = self.loop_repeats
        s['log']['path length'] = self.path_length

        s['allen trace']['min length'] = min([ len(T) for T in self.log ])
        s['allen trace']['median length'] = median([ len(T) for T in self.log ])
        s['allen trace']['max length'] = max([ len(T) for T in self.log ])

        s['mapped trace']['min length'] = min([ len(T) for T in self.mapped_log ])
        s['mapped trace']['median length'] = median([ len(T) for T in self.mapped_log ])
        s['mapped trace']['max length'] = max([ len(T) for T in self.mapped_log ])

        s['symbol']['number'] = len( self.symbols )
        s['symbol']['frecuency'] = {
            'min'  : min(  T.count(s) for T in self.mapped_log for s in self.symbols  ),
            'mean' : mean( T.count(s) for T in self.mapped_log for s in self.symbols  ),
            'max'  : max(  T.count(s) for T in self.mapped_log for s in self.symbols  )
        }
        return s
    
    def trace(self):
        arbitrary_serial = self.L_serials[randint(0, len(self.L_serials)-1)]

        walk = []
        for s in arbitrary_serial:

            loops = [ list(a) for a in self.L_loops if a[0] == s]
            if loops:
                arbitrary_loop = loops[randint(0, len(loops)-1)]
                walk += (arbitrary_loop * randint(0, self.loop_repeats) + [s])
            else:
                walk.append(s)
        return walk
    

    def generate(self):
        L = []
        for i in range(self.N):
            T = "".join( self.trace() )
            L.append(T)
        self.generated_log = L

        
class Alphabet():
    _symbols = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    _noisy   = list(",./;':|\'!^*&#$@`~")

    def __init__(self):
        self._used_symbols = []
        self.symbol = self.create_symbols( self._symbols )
        self.noisy = self.create_symbols( self._noisy )
    
    def create_symbols(self, symbols):
        def combine(A,B):
            return [ a+b for a in A for b in B ]
        used = symbols[:]
        stack = used[:]
        while True:
            nxt = stack.pop(0)
            if not len(stack):
                stack = combine( used, symbols )
                used = stack[:]
            yield nxt
            
    def next(self, n=1):
        return [ next(self.symbol) for i in range(n) ]

    def noise(self, n=1):
        return [ next(self.noisy) for i in range(n) ]
