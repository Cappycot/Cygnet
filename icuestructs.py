from ctypes import c_bool, c_double, c_int, c_char_p, POINTER, Structure


class CorsairProtocolDetails(Structure):
    """
    Structure representing protocol details
    """
    __slots__ = [
        "sdkVersion",
        "serverVersion",
        "sdkProtocolVersion",
        "serverProtocolVersion",
        "breakingChanges"
    ]

    _fields_ = [
        ("sdkVersion", c_char_p),
        ("serverVersion", c_char_p),
        ("sdkProtocolVersion", c_int),
        ("serverProtocolVersion", c_int),
        ("breakingChanges", c_bool)
    ]


class CorsairLedPosition(Structure):
    """
    Structure representing a LED position
    """
    _fields_ = [
        ("ledId", c_int),
        ("top", c_double),
        ("left", c_double),
        ("height", c_double),
        ("width", c_double)
    ]


class CorsairLedPositions(Structure):
    """
    Structure representing LED positions
    """
    _fields_ = [
        ("numberOfLeds", c_int),
        ("pLedPosition", POINTER(CorsairLedPosition))
    ]


class CorsairLedColor(Structure):
    """
    Structure representing a LED color
    """
    _fields_ = [
        ("ledId", c_int),
        ("r", c_int),
        ("g", c_int),
        ("b", c_int)
    ]

    def __init__(self, led_id, r, g, b):
        """
        Args:
            led_id (CLK or int): The LED id you want to set
            r (int): Red component value
            g (int): Green component value
            b (int): You guessed it! Blue component value
        """
        # led_id = led_id.value if isinstance(led_id, CLK) else led_id
        super(CorsairLedColor, self).__init__(led_id, r, g, b)
