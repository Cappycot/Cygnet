import ctypes
from icuestructs import *
from json import load
from os import getcwd, listdir
from os.path import join
from pydub.utils import mediainfo
from pygame import mixer
from random import randint
from serial import Serial
from time import sleep, time

folder = "C:/Program Files (x86)/Steam/steamapps/common/Beat Saber/CustomSongs"
songname = None  # Use None for randomized songs.
diffs = ["ExpertPlus", "Expert", "Hard", "Normal", "Easy"]
fastlimit = 200
slowlimit = 100
subdiv = 0.5
tick = 0.005

use_serial = True
baud = 115200
port = "COM4"

mainsubdiv = subdiv


class Ring:
    def __init__(self, start):
        self.angle = 0
        self.light = 0
        self.speed = 0
        self.start = start
        self.value = 0


class Slash:
    def __init__(self, layer, seq, time, type):
        self.index = 0
        self.layer = layer
        self.length = len(seq)
        self.seq = seq
        self.next = None
        self.time = time
        self.type = type


class Strip:
    def __init__(self, start):
        self.light = 0
        self.start = start
        self.value = 0


# Cut sequences for Corsair LL Series fans.
seq = [
    [  # Up
        [[8], [7], [2, 6], [1, 5], [0, 4], [15], [14]],
        [[8], [9], [2, 10], [3, 11], [0, 12], [13], [14]],
    ],
    [  # Down
        [[14], [15], [0, 4], [1, 5], [2, 6], [7], [8]],
        [[14], [9], [0, 12], [3, 11], [2, 10], [9], [8]]
    ],
    [  # Left
        [[11], [10, 12], [3], [0, 2], [1], [4, 6], [5]],
        [[11], [10, 12], [3], [0, 2], [1], [4, 6], [5]]
    ],
    [  # Right
        [[5], [4, 6], [1], [0, 2], [3], [10, 12], [11]],
        [[5], [4, 6], [1], [0, 2], [3], [10, 12], [11]]
    ],
    [  # Up-Left
        [[9], [8], [2, 7], [1, 6], [5], [4]],
        [[10], [11], [3, 12], [0, 13], [14], [15]]
    ],
    [  # Up-Right
        [[6], [5], [1, 4], [0, 15], [14], [13]],
        [[7], [8], [2, 9], [3, 10], [11], [12]]
    ],
    [  # Down-Left
        [[13], [14], [0, 15], [1, 4], [5], [6]],
        [[12], [11], [3, 10], [2, 9], [8], [7]]
    ],
    [  # Down-Right
        [[4], [5], [1, 6], [2, 7], [8], [9]],
        [[15], [14], [0, 13], [3, 12], [11], [10]]
    ],
    [  # Center
        [[0, 1, 2, 3], [5, 8, 11, 14], [6, 7, 9, 10, 12, 13, 14, 15]],
        [[0, 1, 2, 3], [5, 8, 11, 14], [6, 7, 9, 10, 12, 13, 14, 15]]
    ]
]

# Set up iCue

icue = ctypes.cdll.LoadLibrary(join(getcwd(), "CUESDK.x64_2015.dll"))

icue.CorsairPerformProtocolHandshake.restype = CorsairProtocolDetails

icue.CorsairRequestControl.argtypes = [ctypes.c_int]
icue.CorsairRequestControl.restype = ctypes.c_bool

icue.CorsairReleaseControl.restype = ctypes.c_bool

icue.CorsairGetLedPositionsByDeviceIndex.argtypes = [ctypes.c_int]
icue.CorsairGetLedPositionsByDeviceIndex.restype = ctypes.POINTER(CorsairLedPositions)

icue.CorsairSetLedsColors.argtypes = [ctypes.c_int, ctypes.POINTER(CorsairLedColor)]
icue.CorsairSetLedsColors.restype = ctypes.c_bool

icue.CorsairSetLedsColorsAsync.argtypes = [ctypes.c_int, ctypes.POINTER(CorsairLedColor), ctypes.c_void_p,
                                           ctypes.c_void_p]
icue.CorsairSetLedsColorsAsync.restype = ctypes.c_bool

icue.CorsairSetLedsColorsBufferByDeviceIndex.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(CorsairLedColor)]
icue.CorsairSetLedsColorsBufferByDeviceIndex.restype = ctypes.c_bool

# Do handshake.
icue.CorsairPerformProtocolHandshake()
if use_serial:
    ser = Serial()
    ser.port = port
    ser.baudrate = baud
    ser.setDTR(False)
    ser.open()
    ser.write(bytes([32, 3]))
lastpin13 = False
lastpled = 0

# See device count.
print("{} iCUE devices found.".format(icue.CorsairGetDeviceCount()))

cmdr = None
polaris = None
stand = None
void = None
for i in range(icue.CorsairGetDeviceCount()):
    device = icue.CorsairGetLedPositionsByDeviceIndex(i)
    lasterror = icue.CorsairGetLastError()
    if lasterror != 0:
        print("Device {} resulted in error {}.".format(i, lasterror))
        continue
    device = device.contents
    print("{} leds found on device {}.".format(device.numberOfLeds, i + 1))
    if device.numberOfLeds == 136:
        cmdr = device
    elif device.numberOfLeds == 15:
        polaris = device
    elif device.numberOfLeds == 9:
        stand = device
    elif device.numberOfLeds == 2:
        void = device
if cmdr is None or polaris is None or stand is None:
    print("Some device wasn't found.")
    exit(1)

# print(cmdr.pLedPosition[0].ledId)
# print(cmdr.pLedPosition[cmdr.numberOfLeds - 1].ledId)
cmdr_amt = cmdr.numberOfLeds
cmdr_led = (CorsairLedColor * cmdr_amt)()
rings = [Ring(80), Ring(64), Ring(48)]
strips = [Strip(96), Strip(106)]
cmdr_rgb = [[0, 0, 0]] * cmdr_amt
for i in range(cmdr_amt):  # Still need to allocate new objects into memory.
    cmdr_rgb[i] = [0, 0, 0]

polaris_amt = polaris.numberOfLeds
polaris_led = (CorsairLedColor * polaris_amt)()
polaris_pos = []  # Ok, Corsair. Ok.
polaris_rgb = [[0, 0, 0]] * polaris_amt
for i in range(polaris_amt):
    polaris_pos.append(polaris.pLedPosition[i].ledId)
    polaris_rgb[i] = [0, 0, 0]
polaris_pos.sort()

stand_amt = stand.numberOfLeds
stand_led = (CorsairLedColor * stand_amt)()
stand_pos = []
stand_rgb = [[0, 0, 0]] * stand_amt
for i in range(stand_amt):
    stand_pos.append(stand.pLedPosition[i].ledId)
    stand_rgb[i] = [0, 0, 0]
stand_pos.sort()

void_amt = void.numberOfLeds
void_led = (CorsairLedColor * void_amt)()
void_rgb = [0, 0, 0]
void_prev = [0, 0, 0]
# for i in range(void_amt):
# void_rgb[i] = [0, 0, 0]

# Request lighting control.
icue.CorsairRequestControl(0)

# Song Specific
last_song = None
random_song = songname is None

# Play Songs
while True:
    # Randomize songs.
    if random_song:
        songs = listdir(folder)
        if last_song in songs:
            songs.remove(last_song)
        songname = songs[randint(0, len(songs) - 1)]
        last_song = songname

    print("Loading {}...".format(songname))

    info = load(open("{}/{}/info.json".format(folder, songname), "r"))

    bpm = info["beatsPerMinute"]
    infobpm = bpm
    music = None
    diff = None

    for diff in diffs:
        for difficulty in info["difficultyLevels"]:
            if difficulty["difficulty"].lower() == diff.lower():
                print("Found {} difficulty.".format(diff))
                diff = difficulty["jsonPath"]
                music = "{}/{}/{}".format(folder, songname, difficulty["audioPath"])
                break
        if music is not None:
            break
    if music is None:
        print("Unable to find difficulty for {}.".format(songname))
        continue

    song = load(open("{}/{}/{}".format(folder, songname, diff), "r"))
    # Some difficulty listings use a different bpm than the info bpm.
    if "_beatsPerMinute" in song:
        bpm = int(song["_beatsPerMinute"])
        subdiv = mainsubdiv * bpm / infobpm
        if bpm < slowlimit and infobpm < slowlimit:
            subdiv /= 2
        elif bpm > fastlimit and infobpm > fastlimit:
            subdiv *= 2
    else:
        subdiv = mainsubdiv
        if bpm < slowlimit:
            subdiv /= 2
        elif bpm > fastlimit:
            subdiv *= 2
    print("BPM: {}".format(bpm))
    spb = 60 / bpm
    rgbdec = 255 * bpm / (60 * subdiv / tick)
    events = song["_events"]
    notes = song["_notes"]
    for event in events:
        event["_time"] = event["_time"] * spb * 1000
    for note in notes:
        note["_time"] = note["_time"] * spb * 1000

    offset = 0 if len(notes) == 0 else int(notes[0]["_time"])
    if len(events) > 0:
        if len(notes) == 0:
            offset = int(events[0]["_time"])
        else:
            offset = min(offset, int(events[0]["_time"]))
    if offset < 0:
        offset = 0

    num_events = len(events)
    num_notes = len(notes)

    current_event = 0
    current_note = 0
    slashes = None

    # test_correction = 1000
    corrected = False
    small_incr = -1
    small_lights = [0] * 40
    small_rate = spb * subdiv * 100
    small_time = 0
    small_zoom = -1

    mixer.quit()
    mixer.init(int(mediainfo(music)["sample_rate"]))
    mixer.music.load(music)
    print("Start run.")
    # input("Enter to continue...")
    initial = int(time() * 1000)
    mixer.music.play()
    print("Now playing.")
    # Correct pygame get_pos timing
    sleep(offset / 1000)
    final = mixer.music.get_pos()
    offset = final - offset
    # print(offset)

    while mixer.music.get_busy():
        pos = mixer.music.get_pos() - offset
        for i in range(cmdr_amt):
            for j in range(0, 3, 2):
                cmdr_rgb[i][j] -= rgbdec
                if cmdr_rgb[i][j] < 0:
                    cmdr_rgb[i][j] = 0

        corrected = False

        if 0 <= small_zoom < 10 and pos >= small_time:
            small_time = pos + small_rate
            small_zoom += small_incr

        # Trigger Various Events
        while current_event < num_events and pos >= events[current_event]["_time"]:
            event = events[current_event]
            current_event += 1
            if not corrected:
                final = int(time() * 1000)
                offset = round((mixer.music.get_pos() + offset - final + initial) / 2)
                # print(offset)
                corrected = True
            event_type = event["_type"]
            event_value = event["_value"]
            if event_type == 0:  # Back Top Lasers
                strips[0].value = event_value
                strips[0].light = 0 if event_value == 0 else 255
            elif 1 <= event_type <= 3:  # Track Ring Neons, Left Lasers, Right Lasers
                ring = rings[event_type - 1]
                ring.value = event_value
                ring.light = 0 if event_value == 0 else 255
            elif event_type == 4:  # Bottom/Back/Side Lasers
                strips[1].value = event_value
                strips[1].light = 0 if event_value == 0 else 255
            elif event_type == 8:  # Large Rings Spin
                rings[0].speed = randint(4, 20) * (-1 if randint(0, 1) == 0 else 1) * 90 * bpm * tick / 120
            elif event_type == 9:  # Small Rings Zoom
                small_incr *= -1
                if small_zoom < 0 or small_zoom >= 10:
                    small_zoom += small_incr
            elif event_type == 12:  # Left(?) Ring Rotation
                rings[1].speed = event_value * 90 * bpm * tick / 120
            elif event_type == 13:  # Right(?) Ring Rotation
                rings[2].speed = event_value * 90 * bpm * tick / 120
            elif event_type == 14:  # BPM Change
                print("We can't handle that shit here.")

        # Create Note Slashes
        while current_note < num_notes and pos >= notes[current_note]["_time"]:
            note = notes[current_note]
            current_note += 1
            if note["_type"] > 1:
                continue
            if not corrected:
                final = int(time() * 1000)
                offset = round((mixer.music.get_pos() + offset - final + initial) / 2)
                # print(offset)
                corrected = True
            slash = Slash(note["_lineLayer"], seq[note["_cutDirection"]][note["_type"]], note["_time"], note["_type"])
            slash.next = slashes
            slashes = slash
            for i in range(116, 126):
                if note["_type"] == 0:
                    cmdr_rgb[i][0] = 255
                else:
                    cmdr_rgb[i][2] = 255

        # Reset Top Strip
        for i in range(126, cmdr_amt):
            cmdr_rgb[i][0] = cmdr_rgb[i][2] = 0

        # for ring in rings:
        for r in range(0, 3):
            ring = rings[r]
            if ring.speed == 0 and ring.angle % 30 != 0:
                ring.angle = int(ring.angle + (1 if ring.angle % 30 > 15 else -1))
            else:
                ring.angle += ring.speed
            ring.angle %= 90
            if (ring.value == 2 or ring.value == 6) and ring.light < 128:
                ring.light = 128
            if ring.value > 4:  # Red
                if r > 0:
                    for i in range(126, cmdr_amt):
                        cmdr_rgb[i][0] = max(cmdr_rgb[i][0], ring.light)
                    void_rgb[0] = max(void_rgb[0], ring.light)
                for i in range(16):
                    cmdr_rgb[ring.start + i][2] = 0
                    if i < 4:
                        cmdr_rgb[ring.start + i][0] = ring.light
                    elif i % 3 == 2:
                        if ring.angle < 30:
                            cmdr_rgb[ring.start + i][0] = ring.light * (30 - ring.angle) / 30
                        elif ring.angle > 60:
                            cmdr_rgb[ring.start + i][0] = ring.light * (ring.angle - 60) / 30
                        else:
                            cmdr_rgb[ring.start + i][0] = 0
                    elif i % 3 == 0 and 0 < ring.angle < 60:
                        cmdr_rgb[ring.start + i][0] = ring.light * (1 - abs(30 - ring.angle) / 30)
                    elif i % 3 == 1 and 30 < ring.angle < 90:
                        cmdr_rgb[ring.start + i][0] = ring.light * (1 - abs(60 - ring.angle) / 30)
                    else:
                        cmdr_rgb[ring.start + i][0] = 0
            else:
                if r > 0:
                    for i in range(126, cmdr_amt):
                        cmdr_rgb[i][2] = max(cmdr_rgb[i][2], ring.light)
                    void_rgb[2] = max(void_rgb[2], ring.light)
                for i in range(16):
                    cmdr_rgb[ring.start + i][0] = 0
                    if i < 4:
                        cmdr_rgb[ring.start + i][2] = ring.light
                    elif i % 3 == 2:
                        if ring.angle < 30:
                            cmdr_rgb[ring.start + i][2] = ring.light * (30 - ring.angle) / 30
                        elif ring.angle > 60:
                            cmdr_rgb[ring.start + i][2] = ring.light * (ring.angle - 60) / 30
                        else:
                            cmdr_rgb[ring.start + i][2] = 0
                    elif i % 3 == 0 and 0 < ring.angle < 60:
                        cmdr_rgb[ring.start + i][2] = ring.light * (1 - abs(30 - ring.angle) / 30)
                    elif i % 3 == 1 and 30 < ring.angle < 90:
                        cmdr_rgb[ring.start + i][2] = ring.light * (1 - abs(60 - ring.angle) / 30)
                    else:
                        cmdr_rgb[ring.start + i][2] = 0
            if ring.value % 4 != 1:
                ring.light -= rgbdec
                if ring.light < 0:
                    ring.light = 0

        if rings[0].speed < 0:
            rings[0].speed += bpm / 60 * tick
            if rings[0].speed > 0:
                rings[0].speed = 0
        else:
            rings[0].speed -= bpm / 60 * tick
            if rings[0].speed < 0:
                rings[0].speed = 0

        for strip in strips:
            if (strip.value == 2 or strip.value == 6) and strip.light < 128:
                strip.light = 128
            if strip.value > 4:
                for i in range(10):
                    cmdr_rgb[strip.start + i][0] = strip.light
                    cmdr_rgb[strip.start + i][2] = 0
            else:
                for i in range(10):
                    cmdr_rgb[strip.start + i][0] = 0
                    cmdr_rgb[strip.start + i][2] = strip.light
            if strip.value % 4 != 1:
                strip.light -= rgbdec
                if strip.light < 0:
                    strip.light = 0

        # Hard-coded Small Zoom Lights
        for i in range(40):
            small_lights[i] -= rgbdec
            if i % 10 == small_zoom:
                small_lights[i] = 128
            elif small_lights[i] < 0:
                small_lights[i] = 0
            cmdr_rgb[96 + i][0] = max(cmdr_rgb[96 + i][0], small_lights[i])
            cmdr_rgb[96 + i][2] = max(cmdr_rgb[96 + i][2], small_lights[i])
            if i < 30:
                if 0 < i < 9:
                    small_stand = (9 - i) % 8 + 1
                    stand_rgb[small_stand][0] = stand_rgb[small_stand][1] = stand_rgb[small_stand][2] = small_lights[i]
                if i % 2 == 0:
                    small_polaris = int(i / 2)
                    polaris_rgb[small_polaris][0] = polaris_rgb[small_polaris][1] = polaris_rgb[small_polaris][2] = max(
                        small_lights[i], small_lights[i + 1])
        stand_rgb[0][0] = stand_rgb[0][1] = stand_rgb[0][2] = small_lights[0 if small_incr == 1 else 9]

        prev = None
        slash = slashes
        while slash is not None:
            if pos >= slash.time:
                fan = (2 - slash.layer) * 16
                for i in slash.seq[slash.index]:
                    if slash.type == 0:
                        cmdr_rgb[fan + i][0] = 255
                    else:
                        cmdr_rgb[fan + i][2] = 255
                slash.index += 1
                slash.time += spb * subdiv * 1000 / slash.length
            if slash.index < slash.length:
                prev = slash
            elif prev is not None:
                prev.next = slash.next
            else:
                slashes = slash.next
            slash = slash.next

        # Calculate Commander
        for i in range(cmdr_amt):
            cmdr_rgb[i][1] = min(cmdr_rgb[i][0], cmdr_rgb[i][2])  # Calculate green.
            cmdr_led[i] = CorsairLedColor(cmdr.pLedPosition[i].ledId, int(cmdr_rgb[i][0]), int(cmdr_rgb[i][1]),
                                          int(cmdr_rgb[i][2]))
        icue.CorsairSetLedsColorsAsync(cmdr_amt, ctypes.cast(cmdr_led, ctypes.POINTER(CorsairLedColor)), None, None)

        # Calculate Polaris
        if strips[1].value > 4:  # Red
            for i in range(polaris_amt):
                polaris_rgb[i][0] = max(polaris_rgb[i][0], strips[1].light)
        else:
            for i in range(polaris_amt):
                polaris_rgb[i][2] = max(polaris_rgb[i][2], strips[1].light)
        for i in range(polaris_amt):
            polaris_led[i] = CorsairLedColor(polaris_pos[i], int(polaris_rgb[i][0]), int(polaris_rgb[i][1]),
                                             int(polaris_rgb[i][2]))
        icue.CorsairSetLedsColorsAsync(polaris_amt, ctypes.cast(polaris_led, ctypes.POINTER(CorsairLedColor)), None,
                                       None)

        # Calculate Stand
        if rings[0].value > 4:  # Red
            stand_rgb[0][0] = max(stand_rgb[0][0], rings[0].light)
        else:
            stand_rgb[0][2] = max(stand_rgb[0][2], rings[0].light)
        if strips[0].value > 4:  # Red
            for i in range(1, stand_amt, 1):
                stand_rgb[i][0] = max(stand_rgb[i][0], strips[0].light)
        else:
            for i in range(1, stand_amt, 1):
                stand_rgb[i][2] = max(stand_rgb[i][2], strips[0].light)
        for i in range(stand_amt):
            stand_led[i] = CorsairLedColor(stand_pos[i], int(stand_rgb[i][0]), int(stand_rgb[i][1]),
                                           int(stand_rgb[i][2]))
        icue.CorsairSetLedsColorsAsync(stand_amt, ctypes.cast(stand_led, ctypes.POINTER(CorsairLedColor)), None, None)

        # Calculate Void
        void_rgb[1] = min(void_rgb[0], void_rgb[2])
        if void_prev != void_rgb:
            void_prev[0] = void_rgb[0]
            void_prev[1] = void_rgb[1]
            void_prev[2] = void_rgb[2]
            for i in range(void_amt):
                void_led[i] = CorsairLedColor(void.pLedPosition[i].ledId, int(void_rgb[0]), int(void_rgb[1]),
                                              int(void_rgb[2]))
            icue.CorsairSetLedsColorsAsync(void_amt, ctypes.cast(void_led, ctypes.POINTER(CorsairLedColor)), None, None)
        void_rgb[0] = void_rgb[1] = void_rgb[2] = 0

        if use_serial and ser.out_waiting == 0:
            serout = int(rings[0].light) | 3
            pin13 = serout > 130
            if lastpin13 != pin13:
                lastpin13 = pin13
                ser.write(bytes([96 if pin13 else 32]))
            if lastpled != serout:
                lastpled = serout
                ser.write(bytes([serout]))
        sleep(tick)

    # print(mixer.music.get_pos())
    print("End run.")

    for i in range(cmdr_amt):
        cmdr_rgb[i][0] = cmdr_rgb[i][1] = cmdr_rgb[i][2] = 0
        cmdr_led[i] = CorsairLedColor(cmdr.pLedPosition[i].ledId, 0, 0, 0)
    icue.CorsairSetLedsColorsAsync(cmdr_amt, ctypes.cast(cmdr_led, ctypes.POINTER(CorsairLedColor)), None, None)
    for i in range(polaris_amt):
        polaris_rgb[i][0] = polaris_rgb[i][1] = polaris_rgb[i][2] = 0
        polaris_led[i] = CorsairLedColor(polaris.pLedPosition[i].ledId, 0, 0, 0)
    icue.CorsairSetLedsColorsAsync(polaris_amt, ctypes.cast(polaris_led, ctypes.POINTER(CorsairLedColor)), None, None)
    for i in range(stand_amt):
        stand_rgb[i][0] = stand_rgb[i][1] = stand_rgb[i][2] = 0
        stand_led[i] = CorsairLedColor(stand.pLedPosition[i].ledId, 0, 0, 0)
    icue.CorsairSetLedsColorsAsync(stand_amt, ctypes.cast(stand_led, ctypes.POINTER(CorsairLedColor)), None, None)
    for i in range(void_amt):
        void_led[i] = CorsairLedColor(void.pLedPosition[i].ledId, 0, 0, 0)
    icue.CorsairSetLedsColorsAsync(void_amt, ctypes.cast(void_led, ctypes.POINTER(CorsairLedColor)), None, None)

    # Set serial back.
    if use_serial:
        ser.write(bytes([32, 3]))
    lastpin13 = False
    lastpled = 0

    # mixer.music.get_busy()
    mixer.music.stop()

# Release lighting control.
icue.CorsairReleaseControl(0)
ser.close()
