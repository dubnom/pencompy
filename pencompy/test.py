"""
Test the pencom interface.
"""
from time import sleep
from pencompy import Pencompy

def _callback(board, relay, oldState, newState):
    print(board, relay, oldState, newState)

def _main():
    pen = Pencompy('192.168.2.55', 4007, callback=_callback)
    for trial in range(5):
        pen.set(0, 0, trial % 2 == 0)
        sleep(7.)
    pen.set(0, 0, False)
    pen.close()

_main()
