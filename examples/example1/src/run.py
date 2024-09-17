import numpy as np
from task import Foo, thing
foo = Foo(1,"hello", np.arange(3))
foo.task()

thing('text', foo)