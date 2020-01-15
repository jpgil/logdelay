import random

class synthetic_logs:
    _gens = []
    _symbols = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    _noisy   = list("abcdefghijklmnopqrstuvwxyz")
    
    def __init__(self):
        self._gens = []
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
            
            
    def generate_instances(self, instances=5):
        self.instances = [ self.generate_trace() for i in range(instances) ]
        return self.instances

    def generate_trace(self):
        if len(self._gens) == 0:
            self.symbol = self.create_symbols( self._symbols )
            return [ (i, next(self.symbol) ) for i in range(5) ]
        else:
            trace = []
            for generator in self._gens:
                trace = trace + generator.generate_trace()
            return sorted(trace, key=lambda e: e[0])
            #return trace
            
    def show_instances(self, head=10):
        for i in range( min(head, len(self.instances))  ):
            trace = []
            for t, l in self.instances[i]:
                trace.append(l)
            print("%3d : [%s]" % (i+1, " ".join(trace)))
            
    def add(self, generator):
        generator.log = self
        self._gens.append(generator)
        
    def describe(self):
        if len(self._gens) == 0:
            return []
        else:
            desc = {}
            desc['generators'] = []
            for gen in self._gens:
                desc['generators'].append( gen.describe() )
            return desc
        
class noisy_path:
    def __init__(self, every, num_symbols, count):
        self.every = every
        self.num_symbols = num_symbols
        self.count = count
        self.noise = False
        self.last = []
    def generate_trace(self):
        if not self.noise:
            self.noise = [ next(self.log.noisy) for i in range(self.num_symbols) ]
        t = 0
        trace = []
        for i in range(self.count):
            trace.append( (t, self.noise[ random.randint(0, len(self.noise)-1) ] ) )
            t += self.every
            
        self.last = trace
        return self.last

    
    def describe(self):
        return {
            'class': self.__class__.__name__,
            '#symbols': len(self.noise),
            'example': " ".join([b for (a,b) in self.last[:10] ]),
        }
    
class serial_path:
    def __init__(self, size, every, error=0, probability=1):
        self.every = every
        self.size = size
        self.error = error
        self.probability = probability
        self.path = False
        self.last = [ ]
        
    def generate_trace(self):
        if not self.path:
            self.path = [ next(self.log.symbol) for i in range(self.size) ]
        t = random.randint(0, self.error)
        trace = []
        for s in self.path:
            trace.append( (t, s) )
            err = random.randint(-self.error, self.error)
            t = max( t, t + self.every + err )
        self.last = trace
        if random.random() < self.probability:
            return self.last
        else:
            return []

    
    def describe(self):
        return {
            'class': self.__class__.__name__,
            '#symbols': len(self.path),
            'example': " ".join([b for (a,b) in self.last[:10] ]),
            'error' : self.error,
            'probability' : self.probability
        }