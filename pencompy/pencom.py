"""
Pencom implements the "Switch" interface to control one or more banks of relays
over an Ethernet connection.  The relays are connected through RS232 to an
RS232 to Ethernet convertor (NPort), and telnet is used as the protocol.
"""
import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import Switch, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pencompy==0.0.1']

_LOGGER = logging.getLogger(__name__)

# Number of boards connected to the serial port
CONF_BOARDS = 'boards'

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT): cv.port,
    vol.Optional(CONF_BOARDS,1): cv.int,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Pencom relay platform (pencompy)."""
    import pencompy

    # Assign configuration variables.
    host     = config.get(CONF_HOST)
    port     = config.get(CONF_PORT)
    boards   = config.get(CONF_BOARDS)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    # Setup connection with devices/cloud.
    # FIX: Add support for username and password to pencompy.
    try:
        hub = pencompy.pencompy(host, port, boards=boards)
    except:
        _LOGGER.error("Could not connect to pencompy.")
        return

    # Add devices.
    for board in range(boards):
        for relay in range(RELAYS_PER_BOARD):
            add_devices(PencomRelay(hub, board, relay))


class PencomRelay(Switch):
    """Representation of a pencom relay."""
    def __init__(self, hub, board, relay):
        self._hub   = hub
        self._board = board
        self._relay = relay
        self._state = None
        self._name = "Relay %d:%d" % (board, relay)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    def turn_on(self, **kwargs):
        self._hub.set(self._board, self._relay, True)

    def turn_off(self, **kwargs):
        self._hub.set(self._board, self._relay, False)

    def update(self):
        self._state = self._hub.get(self._board, self._relay)
