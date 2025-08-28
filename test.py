import gc
import sys

class Dummy:
    def __del__(self):
        print("Dummy collected")

def test():
    obj = Dummy()
    return

test()
gc.collect()
# -> "Dummy collected" (immediate)

def test_leak():
    obj = Dummy()
    frame = sys._getframe()  # artificially keep frame alive
    return frame

f = test_leak()
gc.collect()
# -> nothing collected (obj survives, because frame keeps locals)

def test_fix():
    obj = Dummy()
    frame = sys._getframe()
    obj = None        # clear reference before frame escapes
    return frame

f = test_fix()
gc.collect()
# -> "Dummy collected"
