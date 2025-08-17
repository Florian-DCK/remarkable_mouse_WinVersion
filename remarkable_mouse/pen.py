# Variable globale pour activer/désactiver les gestures (désactivé par défaut)
gestures_enabled = False
import logging
import struct
import ctypes
import time
from screeninfo import get_monitors

from .codes import codes, types
from .common import get_monitor, remap, wacom_max_x, wacom_max_y, log_event
from ctypes import *
from ctypes.wintypes import *


logging.basicConfig(format='%(message)s')
log = logging.getLogger('remouse')
log.setLevel(logging.INFO)  # Affiche les logs info et supérieurs par défaut

# Constants
# For penMask
PEN_MASK_NONE=            0x00000000 # Default
PEN_MASK_PRESSURE=        0x00000001
PEN_MASK_ORIENTATION=     0x00000002
PEN_MASK_TILT_X=          0x00000004
PEN_MASK_TILT_Y=          0x00000008

# For penFlag
PEN_FLAG_NONE=            0x00000000

# For pointerType
PT_POINTER=               0x00000001 # All
PT_TOUCH=                 0x00000002
PT_PEN=                   0x00000003
PT_MOUSE=                 0x00000004

#For pointerFlags
POINTER_FLAG_NONE=        0x00000000 # Default
POINTER_FLAG_NEW=         0x00000001
POINTER_FLAG_INRANGE=     0x00000002
POINTER_FLAG_INCONTACT=   0x00000004
POINTER_FLAG_FIRSTBUTTON= 0x00000010
POINTER_FLAG_SECONDBUTTON=0x00000020
POINTER_FLAG_THIRDBUTTON= 0x00000040
POINTER_FLAG_FOURTHBUTTON=0x00000080
POINTER_FLAG_FIFTHBUTTON= 0x00000100
POINTER_FLAG_PRIMARY=     0x00002000
POINTER_FLAG_CONFIDENCE=  0x00004000
POINTER_FLAG_CANCELED=    0x00008000
POINTER_FLAG_DOWN=        0x00010000
POINTER_FLAG_UPDATE=      0x00020000
POINTER_FLAG_UP=          0x00040000
POINTER_FLAG_WHEEL=       0x00080000
POINTER_FLAG_HWHEEL=      0x00100000
POINTER_FLAG_CAPTURECHANGED=0x00200000

# Structs Needed
class POINTER_INFO(Structure):
    _fields_=[("pointerType",c_uint32),
              ("pointerId",c_uint32),
              ("frameId",c_uint32),
              ("pointerFlags",c_int),
              ("sourceDevice",HANDLE),
              ("hwndTarget",HWND),
              ("ptPixelLocation",POINT),
              ("ptHimetricLocation",POINT),
              ("ptPixelLocationRaw",POINT),
              ("ptHimetricLocationRaw",POINT),
              ("dwTime",DWORD),
              ("historyCount",c_uint32),
              ("inputData",c_int32),
              ("dwKeyStates",DWORD),
              ("PerformanceCount",c_uint64),
              ("ButtonChangeType",c_int)
              ]
              
class POINTER_PEN_INFO(Structure):
    _fields_=[("pointerInfo",POINTER_INFO),
              ("penFlags",c_int),
              ("penMask",c_int),
              ("pressure", c_uint32),
              ("rotation", c_uint32),
              ("tiltX", c_int32),
              ("tiltY", c_int32)]
              
class DUMMYUNIONNAME(Structure):
   _fields_=[("penInfo",POINTER_PEN_INFO)
              ]

class POINTER_TYPE_INFO(Structure):
   _fields_=[("type",c_uint32),
              ("penInfo",POINTER_PEN_INFO)
              ]


# Initialize Pen info
pointerInfo_pen = POINTER_INFO(pointerType=PT_PEN,
                            pointerId=0,
                            ptPixelLocation=POINT(950, 540),
                            pointerFlags=POINTER_FLAG_NEW)
penInfo = POINTER_PEN_INFO(pointerInfo=pointerInfo_pen,
                                penMask=(PEN_MASK_PRESSURE | PEN_MASK_TILT_X | PEN_MASK_TILT_Y),
                                pressure=0,
                                tiltX=0,
                                tiltY=0)
pointerTypeInfo_pen = POINTER_TYPE_INFO(type=PT_PEN,
                            penInfo=penInfo)

# Initialize Touch info
pointerInfo_touch = POINTER_INFO(pointerType=PT_TOUCH,
                            pointerId=1,
                            ptPixelLocation=POINT(950, 540),
                            pointerFlags=POINTER_FLAG_NEW)
touchInfo = POINTER_PEN_INFO(pointerInfo=pointerInfo_touch,
                                penMask=0,
                                pressure=0,
                                tiltX=0,
                                tiltY=0)
pointerTypeInfo_touch = POINTER_TYPE_INFO(type=PT_TOUCH,
                            penInfo=touchInfo)

device = windll.user32.CreateSyntheticPointerDevice(3, 1, 1)
print("Initialized Pen/Touch Injection as number ", device)
currently_down_pen = False
currently_down_touch = False


def updatePenInfo(down, x=0, y=0, pressure=0, tiltX=0, tiltY=0):
    global currently_down_pen
    if down:
        pointerTypeInfo_pen.penInfo.pointerInfo.pointerFlags = (POINTER_FLAG_DOWN if not currently_down_pen else POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT)
        currently_down_pen = True
    else:
        pointerTypeInfo_pen.penInfo.pointerInfo.pointerFlags = (POINTER_FLAG_UP if currently_down_pen else POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE)
        currently_down_pen = False
    pointerTypeInfo_pen.penInfo.pointerInfo.ptPixelLocation.x = x
    pointerTypeInfo_pen.penInfo.pointerInfo.ptPixelLocation.y = y
    pointerTypeInfo_pen.penInfo.pressure = pressure
    pointerTypeInfo_pen.penInfo.tiltX = tiltX
    pointerTypeInfo_pen.penInfo.tiltY = tiltY

def updateTouchInfo(down, x=0, y=0):
    global currently_down_touch
    if down:
        pointerTypeInfo_touch.penInfo.pointerInfo.pointerFlags = (POINTER_FLAG_DOWN if not currently_down_touch else POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT)
        currently_down_touch = True
    else:
        pointerTypeInfo_touch.penInfo.pointerInfo.pointerFlags = (POINTER_FLAG_UP if currently_down_touch else POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE)
        currently_down_touch = False
    pointerTypeInfo_touch.penInfo.pointerInfo.ptPixelLocation.x = x
    pointerTypeInfo_touch.penInfo.pointerInfo.ptPixelLocation.y = y


def applyPen():
    result = windll.user32.InjectSyntheticPointerInput(device, byref(pointerTypeInfo_pen), 1)
    if (result == False) and (log.level == logging.DEBUG):
        error_code = ctypes.get_last_error()
        print(f"Failed trying to update pen input. Error code: {error_code}")
        print(f"Error message: {ctypes.WinError(error_code).strerror}")

def applyTouch():
    result = windll.user32.InjectSyntheticPointerInput(device, byref(pointerTypeInfo_touch), 1)
    if (result == False) and (log.level == logging.DEBUG):
        error_code = ctypes.get_last_error()
        print(f"Failed trying to update touch input. Error code: {error_code}")
        print(f"Error message: {ctypes.WinError(error_code).strerror}")
        
def read_tablet(rm_inputs, *, orientation, monitor_num, region, threshold, mode):
    """Loop forever and map evdev events to mouse and touch

    Args:
        rm_inputs (dictionary of paramiko.ChannelFile): dict of pen, button, touch input streams
        orientation (str): tablet orientation
        monitor_num (int): monitor number to map to
        region (boolean): whether to selection mapping region with region tool
        threshold (int): pressure threshold
        mode (str): mapping mode
    """

    from screeninfo import get_monitors
    import threading
    monitors = list(get_monitors())
    current_monitor = [monitor_num]
    monitor, _ = get_monitor(region, current_monitor[0], orientation)

    def set_monitor(idx):
        if 0 <= idx < len(monitors):
            current_monitor[0] = idx
            nonlocal monitor
            monitor, _ = get_monitor(region, current_monitor[0], orientation)
            print(f"Switched to monitor {current_monitor[0]}: {monitor}")

    # Expose setter for integration
    read_tablet.set_monitor = set_monitor

    # Flag partagé pour la proximité du stylet
    pen_inrange = {'value': False}
    # Import dynamique du flag touch_enabled du tray_icon
    import sys
    touch_enabled_ref = None
    try:
        tray_icon_mod = sys.modules.get('remarkable_mouse.tray_icon')
        if tray_icon_mod and hasattr(tray_icon_mod, 'create_tray_icon'):
            touch_enabled_ref = tray_icon_mod.create_tray_icon
    except Exception:
        pass

    # Pen thread
    def pen_thread():
        x = y = mapped_x = mapped_y = press = mapped_press = tiltX = tiltY = 0
        stream = rm_inputs['pen']
        event_counter = 0
        SEND_EVERY_N = 5
        while True:
            try:
                data = stream.read(16)
            except TimeoutError:
                continue
            e_time, e_millis, e_type, e_code, e_value = struct.unpack('2IHHi', data)
            if codes[e_type][e_code] == 'ABS_X':
                x = e_value
            if codes[e_type][e_code] == 'ABS_Y':
                y = e_value
            if codes[e_type][e_code] == 'ABS_PRESSURE':
                press = e_value
                mapped_press = int(press* (1024/4095))
            if codes[e_type][e_code] == 'ABS_TILT_X':
                tiltX = int(e_value*(90/6300))
            if codes[e_type][e_code] == 'ABS_TILT_Y':
                tiltY = int(e_value*(90/6300))
            # Détection de la proximité du stylet (INRANGE)
            if codes[e_type][e_code] == 'SYN_REPORT':
                event_counter += 1
                # On considère le stylet "proche" si la pression > 0 ou si on a reçu un event récemment
                pen_inrange['value'] = (press > 0)
                if event_counter % SEND_EVERY_N == 0:
                    mapped_x, mapped_y = remap(
                        x, y,
                        wacom_max_x, wacom_max_y,
                        monitor.width, monitor.height,
                        mode, orientation,
                    )
                    if press > 0:
                        updatePenInfo(True, max(int(monitor.x+mapped_x),0), max(int(monitor.y+mapped_y),0), mapped_press, tiltX, tiltY)
                    else:
                        updatePenInfo(False, max(int(monitor.x+mapped_x),0), max(int(monitor.y+mapped_y),0), mapped_press, tiltX, tiltY)
                    applyPen()

    # Touch thread
    def touch_thread():
        # Fonction utilitaire pour envoyer Ctrl+Z
        def send_ctrl_z():
            log.info("[GESTURE] Envoi de Ctrl+Z")
            VK_CONTROL = 0x11
            VK_Z = 0x5A
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_Z, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_Z, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        x = y = mapped_x = mapped_y = 0
        touch_down = False
        stream = rm_inputs['touch']
        # Multitouch state
        mt_x = mt_y = 0
        # Multitouch slots (slot_id -> tracking_id)
        current_slot = 0
        slot_tracking = {}  # slot_id -> tracking_id
        tracking_slot = {}  # tracking_id -> slot_id
        active_fingers = {}  # tracking_id -> {'down': True, 'x': mt_x, 'y': mt_y}
        last_two_finger_tap = 0
        last_two_finger_pos = None  # (x1, y1, x2, y2)
        last_two_finger_time = 0  # moment où il y a eu exactement deux doigts
        TWO_FINGER_MAX_DIST = 400  # pixels (tolérance augmentée)
        TWO_FINGER_MAX_TIME = 1.0  # secondes (tolérance augmentée)
        global gestures_enabled
        max_fingers_in_tap = 0
        while True:
            try:
                data = stream.read(16)
            except TimeoutError:
                continue
            # Si le stylet est proche ou le touch désactivé, on ignore tous les événements tactiles
            if pen_inrange['value']:
                continue
            if touch_enabled_ref and hasattr(touch_enabled_ref, 'touch_enabled') and not touch_enabled_ref.touch_enabled:
                continue
            e_time, e_millis, e_type, e_code, e_value = struct.unpack('2IHHi', data)
            try:
                code_name = codes[e_type][e_code]
            except Exception:
                code_name = f"UNKNOWN({e_type},{e_code})"

            if code_name == 'ABS_MT_SLOT':
                current_slot = e_value
            elif code_name == 'ABS_MT_TRACKING_ID':
                if e_value == -1:
                    # Fin de contact pour ce slot
                    if current_slot in slot_tracking:
                        tid = slot_tracking[current_slot]
                        if tid in active_fingers:
                            del active_fingers[tid]
                        if tid in tracking_slot:
                            del tracking_slot[tid]
                        del slot_tracking[current_slot]
                        # log.info(f"Touch event: UP [tracking_id={tid}] (fingers={len(active_fingers)})")
                    # Ne rien faire ici, le reset se fait dans le SYN_REPORT
                else:
                    # Nouveau contact pour ce slot
                    slot_tracking[current_slot] = e_value
                    tracking_slot[e_value] = current_slot
                    active_fingers[e_value] = {'down': True, 'x': mt_x, 'y': mt_y}
                    # log.info(f"Touch event: DOWN at ({mt_x}, {mt_y}) [tracking_id={e_value}] (fingers={len(active_fingers)})")
                    # Met à jour le nombre max de doigts actifs pendant ce tap
                    max_fingers_in_tap = max(max_fingers_in_tap, len(active_fingers))
                    if len(active_fingers) == 2:
                        tids = list(active_fingers.keys())
                        f1 = active_fingers[tids[0]]
                        f2 = active_fingers[tids[1]]
                        last_two_finger_pos = (f1['x'], f1['y'], f2['x'], f2['y'])
                        last_two_finger_time = time.time()
                        pass
                        pass
                        pass
                        pass
                        pass
                    elif len(active_fingers) == 1:
                        # Si on pose un seul doigt, on reset la gesture
                        last_two_finger_pos = None
                        last_two_finger_time = 0
                        max_fingers_in_tap = 1
                        # log.debug info removed
                    else:
                        pass
            elif code_name == 'ABS_MT_POSITION_X':
                mt_x = e_value
                # Met à jour la position du doigt courant
                if current_slot in slot_tracking:
                    tid = slot_tracking[current_slot]
                    pass
            elif code_name == 'ABS_MT_POSITION_Y':
                mt_y = e_value
                if current_slot in slot_tracking:
                    tid = slot_tracking[current_slot]
                    pass
            # Injection du touch Windows à chaque SYN_REPORT
            if code_name == 'SYN_REPORT':
                mapped_x, mapped_y = remap(
                    mt_x, mt_y,
                    wacom_max_x, wacom_max_y,
                    monitor.width, monitor.height,
                    mode, orientation,
                )
                is_touching = len(active_fingers) > 0
                # log.debug info removed
                updateTouchInfo(is_touching, max(int(monitor.x+mapped_x),0), max(int(monitor.y+mapped_y),0))
                applyTouch()
                # Détection d'un tap à deux doigts plus tolérante :
                # Si on n'a plus aucun doigt, et que le dernier état à deux doigts date de moins de TWO_FINGER_MAX_TIME
                if len(active_fingers) == 0 and last_two_finger_time > 0 and last_two_finger_pos is not None:
                    if isinstance(last_two_finger_pos, tuple) and len(last_two_finger_pos) == 4:
                        dt = time.time() - last_two_finger_time
                        x1, y1, x2, y2 = last_two_finger_pos
                        dist = ((x1-x2)**2 + (y1-y2)**2) ** 0.5
                        # log.debug info removed
                        if gestures_enabled and dt < TWO_FINGER_MAX_TIME and dist < TWO_FINGER_MAX_DIST and max_fingers_in_tap == 2:
                            log.info("[GESTURE] Condition validée, envoi Ctrl+Z")
                            send_ctrl_z()
                        elif not gestures_enabled:
                            pass
                        else:
                            pass
                            # log.debug info removed
                    else:
                        pass
                        # log.debug info removed
                    last_two_finger_time = 0
                    last_two_finger_pos = None
                    max_fingers_in_tap = 0
            # else: on ne touche plus à last_two_finger_pos ici
            pending_up = None
        # Les positions sont déjà gérées dans la nouvelle logique ci-dessus
        # Bloc supprimé : gestion SYN_REPORT/UP/DEBUG désormais dans la nouvelle logique

    threading.Thread(target=pen_thread, daemon=True).start()
    threading.Thread(target=touch_thread, daemon=True).start()
    while True:
        time.sleep(1)  # Keep main thread alive