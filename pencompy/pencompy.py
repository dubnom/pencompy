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

BOARD_NUM = lambda b: chr(ord('A')+b)
POLLING_FREQ = 2.
CONNECTION_TIMEOUT = 15.0

class Pencompy(Thread):
    """Interface with a Pencom relay controller."""
    # pylint: disable=too-many-instance-attributes
    _polling_thread = None
    _telnet = None
    _running = False
    polling_board = 0

    def __init__(self, host, port, boards=1, callback=None):
        Thread.__init__(self, target=self)
        self._host = host
        self._port = port
        self._callback = callback

        self.boards = boards

        self._connect()
        self.start()

    def _connect(self):
        # Add userID and password
        self._telnet = telnetlib.Telnet(self._host, self._port, CONNECTION_TIMEOUT)
        self._states = [[-1 for _ in range(RELAYS_PER_BOARD)] for _ in range(self.boards)]
        self._polling_thread = Polling(self, POLLING_FREQ)
        self._polling_thread.start()

    def set(self, board, relay, state):
        """Turn a relay on/off."""
        if 0 <= board < self.boards and 0 <= relay < RELAYS_PER_BOARD:
            self.send('%s%s%d' % (BOARD_NUM(board), 'H' if state else 'L', relay+1))
        # FIX: Contemplate throwing an error here

    def get(self, board, relay):
        """Get the relay's state."""
        if 0 <= board < self.boards and 0 <= relay < RELAYS_PER_BOARD:
            return self._states[board][relay]
        # FIX: Contemplate throwing an error or return something
        return -1

    def _update_state(self, relay, new_state):
        if 0 <= relay < RELAYS_PER_BOARD:
            return
        board = self.polling_board
        old_state = self._states[board][relay]
        if old_state != new_state:
            if self._callback:
                self._callback(board, relay, old_state, new_state)
            self._states[board][relay] = new_state

    def send(self, command):
        """Send data to the relay controller."""
        # FIX: ADD LOCK
        # with self._lock:
        # FIX: If error, reconnect
        self._telnet.write((command+'\n').encode('utf8'))

    def run(self):
        self._running = True
        while self._running:
            data = self._telnet.read_until(b'\r', 1.).strip()
            if len(data) > 0:
                bits = int(data)
                mask = 0x0001
                for relay in range(RELAYS_PER_BOARD):
                    self._update_state(relay, (bits & mask) != 0)
                    mask <<= 1

    def close(self):
        """Close the connection."""
        self._running = False
        if self._polling_thread:
            self._polling_thread.halt()
            self._polling_thread = None
        if self._telnet:
            time.sleep(POLLING_FREQ)
            self._telnet.close()
            self._telnet = None


class Polling(Thread):
    """Thread that asks for each board's status at a specified interval."""

    def __init__(self, pencom, delay):
        super(Polling, self).__init__()
        self._pencom = pencom
        self._delay = delay
        self._running = True

    def run(self):
        while self._running:
            for board in range(self._pencom.boards):
                self._pencom.polling_board = board
                self._pencom.send('%sR0' % BOARD_NUM(board))
                time.sleep(self._delay)

    def halt(self):
        """Terminate polling thread."""
        self._running = False
