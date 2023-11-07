import enum
import ctypes
import copy
import os
import typing
import platform

import numpy as np

class CubeProgrammerError(enum.IntEnum):
    NONE = 0                        # Success
    NOT_CONNECTED = -1              # Device not connected
    NO_DEVICE = -2                  # Device not found
    CONNECTION = -3                 # Device connection error
    NO_FILE = -4                    # No such file
    NOT_SUPPORTED = -5              # Operation not supported
    INTERFACE_NOT_SUPPORTED = -6    # Interface not supported
    NO_MEM = -7                     # Insufficient memory
    WRONG_PARAM = -8                # Wrong parameters
    READ_MEM = -9                   # Memory read failure
    WRITE_MEM = -10                 # Memory write failure
    ERASE_MEM = -11                 # Memory erase failure
    UNSUPPORTED_FILE_FORMAT = -12   # File format not supported
    REFRESH_REQUIRED = -13          # Refresh required
    NO_SECURITY = -14               # Security required
    CHANGE_FREQ = -15               # Changer frequency issue
    RDP_ENABLED = -16               # RDP enabled
    UNKNOWN = -99                   # Unknown error

class Verbosity(enum.IntEnum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3

class DebugPort(enum.IntEnum):
    JTAG = 0
    SWD = 1

class DebugConnectMode(enum.IntEnum):
    NORMAL = 0
    HOTPLUG = 1
    UNDER_RESET = 2
    POWER_DOWN = 3
    PRE_RESET = 4

class DebugResetMode(enum.IntEnum):
    SOFTWARE_RESET = 0
    HARDWARE_RESET = 1
    CORE_RESET = 2

class DisplayCallbacks(ctypes.Structure):
    _fields_ = [("init_progressbar", ctypes.CFUNCTYPE(None)),
                ("log_message", ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_wchar_p)),
                ("set_progressbar", ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_int32))]
    
class Frequencies(ctypes.Structure):
    _fields_ = [("jtag_freq", ctypes.c_uint32 * 12),
                ("jtag_freq_count", ctypes.c_uint32),
                ("swd_freq", ctypes.c_uint32 * 12),
                ("swd_freq_count", ctypes.c_uint32)]
    
class DebugConnectParameters(ctypes.Structure):
    _fields_ = [("debug_port", ctypes.c_int32),
                ("index", ctypes.c_int32),
                ("serial_number", ctypes.c_char * 33),
                ("firmware_version", ctypes.c_char *20),
                ("target_voltage", ctypes.c_char * 5),
                ("accessport_count", ctypes.c_int32),
                ("accessport", ctypes.c_int32),
                ("connection_mode", ctypes.c_int32),
                ("reset_mode", ctypes.c_int32),
                ("is_old_firmware", ctypes.c_int32),
                ("frequencies", Frequencies),
                ("frequency", ctypes.c_int32),
                ("is_bridge", ctypes.c_int32),
                ("shared", ctypes.c_int32),
                ("board", ctypes.c_char * 100),
                ("debug_sleep", ctypes.c_int32),
                ("speed", ctypes.c_int32)]
    
class TargetInfoParameters(ctypes.Structure):
    _fields_ = [("device_id", ctypes.c_uint16),
                ("flash_size", ctypes.c_int32),
                ("bootloader_version", ctypes.c_int32),
                ("type", ctypes.c_char * 4),
                ("cpu", ctypes.c_char * 20),
                ("name", ctypes.c_char * 100),
                ("series", ctypes.c_char * 100),
                ("description", ctypes.c_char * 150),
                ("revision_id", ctypes.c_char * 8),
                ("board", ctypes.c_char * 100)]
    
class TargetInfo():
    def __init__(self, target_info_parameters:TargetInfoParameters) -> None:
        self.target_info_parameters = copy.deepcopy(target_info_parameters[0])

    @property
    def device_id(self) -> str:
        return f'{self.target_info_parameters.device_id:X}'
    
    @property
    def name(self) -> str:
        return self.target_info_parameters.name.decode('utf-8')
    
    @property
    def revision_id(self) -> str:
        return self.target_info_parameters.revision_id.decode('utf-8')
    
class STLink():

    def __init__(self, debug_connect_parameters:DebugConnectParameters) -> None:
        self.debug_connect_parameters = copy.deepcopy(debug_connect_parameters)
        self.debug_connect_parameters.connection_mode = DebugConnectMode.UNDER_RESET
        self.debug_connect_parameters.reset_mode = DebugResetMode.HARDWARE_RESET

    @property
    def firmware_version(self) -> str:
        return self.debug_connect_parameters.firmware_version.decode('utf-8')
    
    @property
    def serial_number(self) -> str:
        return self.debug_connect_parameters.serial_number.decode('utf-8')
    
    @property
    def board(self) -> str:
        return self.debug_connect_parameters.board.decode('utf-8')
    
class CubeProgrammerApi():
    dll: typing.ClassVar[ctypes.CDLL]
    display_callbacks: DisplayCallbacks
    
    def __init__(self, path:str) -> None:
        if 'Linux' in platform.system():
            dll_path = os.path.abspath(rf'{path}/lib/libCubeProgrammer_API.so')
            flashloader_path = os.path.abspath(rf'{path}/bin')
        elif 'Window' in platform.system():
            raise NotImplementedError("Platform not supported yet.")
        else:
            raise NotImplementedError("Platform not supported yet.")
        
        self.dll = ctypes.cdll.LoadLibrary(dll_path)
        self.display_callbacks = DisplayCallbacks(
            ctypes.CFUNCTYPE(None)(CubeProgrammerApi._init_progressbar),
            ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_wchar_p)(CubeProgrammerApi._log_message),
            ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_int32)(CubeProgrammerApi._set_progessbar)
        )
        self.dll.setLoadersPath(flashloader_path.encode('utf-8'))
        self.dll.setDisplayCallbacks(self.display_callbacks)
        self.dll.setVerbosityLevel(Verbosity.LEVEL_0)

    def discover(self) -> list[STLink]:
        debug_connect_parameters = ctypes.POINTER(DebugConnectParameters)()
        stlink_count = self.dll.getStLinkList(ctypes.byref(debug_connect_parameters), 0)
        stlinks = [STLink(debug_connect_parameters[i]) for i in range(stlink_count)]
        return stlinks
    
    def connect(self, stlink:STLink) -> CubeProgrammerError:
        return self.dll.connectStLink(stlink.debug_connect_parameters)
    
    def download(self,
                 path:str,
                 address:int,
                 skip_erase:bool,
                 verify:bool) -> CubeProgrammerError:
        return self.dll.donwloadFile(os.path.abspath(path),
                                     address,
                                     int(skip_erase),
                                     int(verify),
                                     "")

    def info(self) -> TargetInfo:
        self.dll.getDeviceGeneralInf.restype = ctypes.POINTER(TargetInfoParameters)
        target_info_parameters = self.dll.getDeviceGeneralInf()
        return TargetInfo(target_info_parameters)
    
    def erase(self) -> CubeProgrammerError:
        return self.dll.massErase()
    
    def read8(self, address:int, size:int) -> list[int]:
        buffer = ctypes.POINTER(ctypes.c_ubyte)()
        status = self.dll.readMemory(address, ctypes.byref(buffer), size)
        if status:
            return []
        buffer = buffer[:size]
        return list(np.array(buffer, np.uint8))
    
    def read32(self, address:int, size:int) -> list[int]:
        buffer = ctypes.POINTER(ctypes.c_uint8)()
        status = self.dll.readMemory(address, ctypes.byref(buffer), size * 4)
        if status:
            return []
        buffer = buffer[:size * 4]
        return list(np.array(buffer, np.uint8).view(np.uint32))
    
    def disconnect(self) -> None:
        self.dll.disconnect()

    def reset(self, mode) -> None:
        return self.dll.reset(mode)

    @staticmethod
    def _init_progressbar() -> None:
        pass

    @staticmethod
    def _log_message(type, message) -> None:
        pass

    @staticmethod
    def _set_progessbar(current, total) -> None:
        pass