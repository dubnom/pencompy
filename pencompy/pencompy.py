"""
Pencompy is a library for controlling Pencom banks of relays.  The
connection is done serially through an RS232 to Ethernet adaptor (NPort)
that implements telnet protocols.

the state for a relay isn't updated until a response from the board or a
polling request occurs.

Michael Dubno - 2018 - New York
"""

from threading import Thread
import time
import telnetlib

RELAYS_PER_BOARD = 8

_boardNumber = lambda b: chr(ord('A')+b)

class pencompy(Thread):
    """Interface with a Pencom relay controller."""

    def __init__(self,host,port,pollingFreq=2.,boards=1,callback=None):
        Thread.__init__(self,target=self)
        self._host = host
        self._port = port
        self._pollingFreq = pollingFreq
        self._boards = boards
        self._callback = callback

        self._pollingBoard = 0

        self._pollingThread = None
        self._telnet = None
        self._running = False
        self._connect()
        self.start()

    def _connect(self):
        # Add userID and password
        self._telnet = telnetlib.Telnet( self._host, self._port )
        self._stateTable = [ [ -1 for r in range(RELAYS_PER_BOARD) ] for b in range(self._boards) ]
        self._pollingThread = PollingThread(self,self._pollingFreq)
        self._pollingThread.start()

    def set(self,board,relay,state):
        if 0 <= board < self._boards and 0 <= relay < RELAYS_PER_BOARD:
            self._send( '%s%s%d' % (_boardNumber(board), 'H' if state else 'L', relay+1))
        # FIX: Contemplate throwing an error here

    def get(self,board,relay):
        if 0 <= board < self._boards and 0 <= relay < RELAYS_PER_BOARD:
            return self._stateTable[ board ][ relay ]
        # FIX: Contemplate throwing an error or return something
        return -1

    def _updateState(self,relay,newState):
        print( "update state:",self._pollingBoard,relay,newState)
        if 0 <= relay < RELAYS_PER_BOARD:
            return
        oldState = self._stateTable[ self._pollingBoard ][ relay ]
        if oldState != newState:
            if self._callback:
                self._callback( board, relay, oldState, newState )
            self._stateTable[ board ][ relay ] = newState

    def _send(self,command):
        # FIX: ADD LOCK
        # with self._lock:
        # FIX: If error, reconnect
        self._telnet.write((command+'\n').encode('utf8'))

    def run(self):
        self._running = True
        while self._running:
            input = self._telnet.read_until(b'\r',1.).strip()
            if len(input) > 0:
                bits = int(input)
                mask = 0x0001
                for r in range(RELAYS_PER_BOARD):
                    self._updateState( r, (bits & mask) != 0 )
                    mask <<= 1

    def close(self):
        self._running = False
        if self._pollingThread:
            self._pollingThread.halt()
            self._pollingThread = None
        if self._telnet:
            time.sleep(self._pollingFreq)
            self._telnet.close()
            self._telnet = None


class PollingThread(Thread):
    """Thread that asks for each board's status at a specified interval"""
    def __init__(self,pencom,delay):
        super(PollingThread,self).__init__()
        self._pencom = pencom
        self._delay = delay

    def run(self):
        self.running = True
        while self.running:
            for board in range(self._pencom._boards):
                self._pencom._pollingBoard = board
                self._pencom._send( '%sR0' %  _boardNumber(board))
                time.sleep(self._delay)

    def halt(self):
        self.running = False
    
