from dataclasses import dataclass
import numpy as np
from hwlib.keywords import EXITIFCOLLECTING, HOMEWORK, KEEP, REPLACE, TOASSIGN



@dataclass 
class Foo:
    idx: int
    name: str
    data: np.ndarray
    
    @HOMEWORK
    def task(self):
        """Tasks require a docstring"""
        out0 = self.idx+1 
        out1 = self.data.sum()
        # can only return variables. This will fail; return self.idx+1, self.data.sum() 
        return out0, out1
    
@HOMEWORK
def thing(input0:str, input1: Foo):
    """Tasks require a docstring"""
    
    if KEEP:
        # comment
        a = 'this is kept'
        b = 'this is kept'        
    c = KEEP('this is kept')
    # comment
    d = 'this line is removed'
    
    if REPLACE:
        a = "this is replaced"
        b = "this as well"
    else:
        a = "with this"
        b = "and this"
        
    c = REPLACE('this is replaced', 'with this')
    
    
    if TOASSIGN:
        a = "this is replaced with None"
        b = "this as well"
    c = TOASSIGN('this is replaced with None')
    
    # comment
    d = 'everything else is deleted'
    out = input0 + input1.name
    return out


