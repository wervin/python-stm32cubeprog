import enum
import ctypes
import copy
import os
import typing
import platform

class Verbosity(enum.IntEnum):
    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3

class DebugPort(enum.IntEnum):
    JTAG = 0
    SWD = 1

class CubeProgrammerError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        message = self._get_error_message(status_code)
        super().__init__(message)

    def __str__(self):
        return f"{super().__str__()} (Status code: {self.status_code})"

    @staticmethod
    def _get_error_message(status_code):
        # Map status codes to error messages
        error_messages = {
            -1: "Device not connected",
            -2: "Device not found",
            -3: "Device connection error",
            -4: "No such file",
            -5: "Operation not supported or unimplemented on this interface",
            -6: "Interface not supported or unimplemented on this platform",
            -7: "Insufficient memory",
            -8: "Wrong parameters",
            -9: "Memory read failure",
            -10: "Memory write failure",
            -11: "Memory erase failure",
            -12: "File format not supported for this kind of device",
            -13: "Refresh required",
            -14: "No security",
            -15: "Changing frequency problem",
            -16: "RDP Enabled error",
            -99: "Other error",
        }
        return error_messages.get(status_code, "Unknown error occurred.")

class CubeProgrammerRegister(enum.IntEnum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    R8 = 8
    R9 = 9
    R10 = 10
    R11 = 11
    R12 = 12
    SP = 13
    LR = 14
    PC = 15

class CubeProgrammerConnectionMode(enum.IntEnum):
    NORMAL = 0
    HOTPLUG = 1
    UNDER_RESET = 2
    POWER_DOWN = 3
    PRE_RESET = 4

class CubeProgrammerResetMode(enum.IntEnum):
    SOFTWARE_RESET = 0
    HARDWARE_RESET = 1
    CORE_RESET = 2

class DisplayCallbacks(ctypes.Structure):
    _fields_ = [("init_progressbar", ctypes.CFUNCTYPE(None)),
                ("log_message", ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_wchar_p)),
                ("set_progressbar", ctypes.CFUNCTYPE(None, ctypes.c_int32, ctypes.c_int32))]
    
class DebugConnectParameters(ctypes.Structure):
    _fields_ = [("debug_port", ctypes.c_int32),
                ("index", ctypes.c_int32),
                ("serial_number", ctypes.c_char * 33),
                ("firmware_version", ctypes.c_char *20),
                ("target_voltage", ctypes.c_char * 5),
                ("access_port_count", ctypes.c_int32),
                ("access_port", ctypes.c_int32),
                ("connection_mode", ctypes.c_int32),
                ("reset_mode", ctypes.c_int32),
                ("old_firmware", ctypes.c_int32),
                ("jtag_freq", ctypes.c_uint32 * 12),
                ("jtag_freq_count", ctypes.c_uint32),
                ("swd_freq", ctypes.c_uint32 * 12),
                ("swd_freq_count", ctypes.c_uint32),
                ("frequency", ctypes.c_int32),
                ("bridge", ctypes.c_int32),
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
    
class CubeProgrammerTargetInfo():
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
    
class CubeProgrammerSTLink():

    def __init__(self, debug_connect_parameters:DebugConnectParameters) -> None:
        self.debug_connect_parameters = copy.deepcopy(debug_connect_parameters)

    @property
    def firmware_version(self) -> str:
        return self.debug_connect_parameters.firmware_version.decode('utf-8')
    
    @property
    def serial_number(self) -> str:
        return self.debug_connect_parameters.serial_number.decode('utf-8')
    
    @property
    def board(self) -> str:
        return self.debug_connect_parameters.board.decode('utf-8')
    
    @property
    def target_voltage(self) -> float:
        return float(self.debug_connect_parameters.target_voltage.decode('utf-8'))
        
    @property
    def connection_mode(self) -> CubeProgrammerConnectionMode:
        return self.debug_connect_parameters.connection_mode
    
    @property
    def reset_mode(self) -> CubeProgrammerResetMode:
        return self.debug_connect_parameters.reset_mode
    
    @property
    def access_port(self) -> int:
        return self.debug_connect_parameters.access_port
    
    @property
    def index(self) -> int:
        return self.debug_connect_parameters.index
    
    @property
    def index(self) -> int:
        return self.debug_connect_parameters.index
    
    @property
    def access_port_count(self) -> int:
        return self.debug_connect_parameters.access_port_count
    
    @property
    def debug_port(self) -> int:
        return self.debug_connect_parameters.debug_port
    
    @property
    def frequency(self) -> int:
        return self.debug_connect_parameters.frequency
    
    @property
    def speed(self) -> int:
        return self.debug_connect_parameters.speed
        
    @property
    def old_firmware(self) -> bool:
        return self.debug_connect_parameters.old_firmware == 1
    
    @property
    def bridge(self) -> bool:
        return self.debug_connect_parameters.bridge == 1
    
    @property
    def shared(self) -> bool:
        return self.debug_connect_parameters.shared == 1
    
    @property
    def debug_sleep(self) -> bool:
        return self.debug_connect_parameters.debug_sleep == 1
    
    @property
    def jtag_frequencies(self) -> list[int]:
        return list(self.debug_connect_parameters.jtag_freq[:self.debug_connect_parameters.jtag_freq_count])

    @property
    def swd_frequencies(self) -> list[int]:
        return list(self.debug_connect_parameters.swd_freq[:self.debug_connect_parameters.swd_freq_count])
    
    @access_port.setter
    def access_port(self, value:int):
        self.debug_connect_parameters.access_port = value

    @frequency.setter
    def frequency(self, value:int):
        self.debug_connect_parameters.frequency = value

    @reset_mode.setter
    def reset_mode(self, value:CubeProgrammerResetMode):
        self.debug_connect_parameters.reset_mode = value

    @connection_mode.setter
    def connection_mode(self, value:CubeProgrammerConnectionMode):
        self.debug_connect_parameters.connection_mode = value
    
    def __str__(self) -> str:
        return f'Board: {self.board}\n'\
               f'Serial Number: {self.serial_number}\n'\
               f'Firmware Version: {self.firmware_version}\n'\
               f'Index: {self.index}\n'\
               f'Connection Mode: {self.connection_mode}\n'\
               f'Reset Mode: {self.reset_mode}\n'\
               f'Access Port Count: {self.access_port_count}\n'\
               f'Access Port: {self.access_port}\n'\
               f'Debug Port: {self.debug_port}\n'\
               f'Old Firmware: {self.old_firmware}\n'\
               f'SWD Frequencies: {self.swd_frequencies}\n'\
               f'JTAG Frequencies: {self.jtag_frequencies}\n'\
               f'Frequency: {self.frequency}\n'\
               f'Bridge: {self.bridge}\n'\
               f'Shared: {self.shared}\n'\
               f'Debug Sleep: {self.debug_sleep}\n'\
               f'Speed: {self.speed}\n'\
               f'Target Voltage: {self.target_voltage}\n'\
    
class CubeProgrammerApi():
    dll: typing.ClassVar[ctypes.CDLL]
    display_callbacks: DisplayCallbacks
    
    def __init__(self, path:str) -> None:
        if 'Linux' in platform.system():
            dll_path = os.path.abspath(rf'{path}/api/lib/libCubeProgrammer_API.so')
            flashloader_path = os.path.abspath(rf'{path}/bin')
        elif 'Window' in platform.system():
            dll_path = os.path.abspath(rf'{path}/api/lib/CubeProgrammer_API.dll')
            flashloader_path = os.path.abspath(rf'{path}/bin')
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

        self.dll.getStLinkEnumerationList.restype = ctypes.c_int32
        self.dll.getStLinkList.restype = ctypes.c_int32
        self.dll.connectStLink.restype = ctypes.c_int32
        self.dll.downloadFile.restype = ctypes.c_int32
        self.dll.getDeviceGeneralInf.restype = ctypes.POINTER(TargetInfoParameters)
        self.dll.massErase.restype = ctypes.c_int32
        self.dll.readMemory.restype = ctypes.c_int32
        self.dll.writeMemory.restype = ctypes.c_int32
        self.dll.readCortexReg.restype = ctypes.c_int32
        self.dll.writeCortexRegistres.restype = ctypes.c_int32
        self.dll.reset.restype = ctypes.c_int32

    def probe(self) -> list[CubeProgrammerSTLink]:
        debug_connect_parameters = ctypes.POINTER(DebugConnectParameters)()
        stlink_count = self.dll.getStLinkEnumerationList(ctypes.byref(debug_connect_parameters), 0)
        stlinks = [CubeProgrammerSTLink(debug_connect_parameters[i]) for i in range(stlink_count)]
        return stlinks
    
    def find(self) -> list[CubeProgrammerSTLink]:
        debug_connect_parameters = ctypes.POINTER(DebugConnectParameters)()
        stlink_count = self.dll.getStLinkList(ctypes.byref(debug_connect_parameters), 0)
        stlinks = [CubeProgrammerSTLink(debug_connect_parameters[i]) for i in range(stlink_count)]
        return stlinks
    
    def connect(self, stlink:CubeProgrammerSTLink) -> None:
        status = self.dll.connectStLink(stlink.debug_connect_parameters)
        if status != 0:
            raise CubeProgrammerError(status)
    
    def download(self,
                 path:str,
                 address:int,
                 skip_erase:bool,
                 verify:bool) -> None:
        status = self.dll.downloadFile(os.path.abspath(path),
                                     address,
                                     int(skip_erase),
                                     int(verify),
                                     "")
        if status != 0:
            raise CubeProgrammerError(status)

    def info(self) -> CubeProgrammerTargetInfo:
        target_info_parameters = self.dll.getDeviceGeneralInf()
        return CubeProgrammerTargetInfo(target_info_parameters)
    
    def mass_erase(self) -> None:
        status = self.dll.massErase()
        if status != 0:
            raise CubeProgrammerError(status)
    
    def read_memory(self, address:int, size:int) -> bytes:
        buffer = ctypes.POINTER(ctypes.c_ubyte)()
        status = self.dll.readMemory(address, ctypes.byref(buffer), size)
        if status != 0:
            raise CubeProgrammerError(status)
        return bytes(buffer[:size])
    
    def write_memory(self, address:int, data: bytes) -> None:
        status = self.dll.writeMemory(address, data, len(data))
        if status != 0:
            raise CubeProgrammerError(status)
        
    def read_register(self, register: CubeProgrammerRegister) -> int:
        data = ctypes.c_uint32()
        status = self.dll.readCortexReg(register, ctypes.byref(data))
        if status != 0:
            raise CubeProgrammerError(status)
        return data.value

    def write_register(self, register: CubeProgrammerRegister, data: int) -> None:
        status = self.dll.writeCortexRegistres(register, data)
        if status != 0:
            raise CubeProgrammerError(status)
    
    def disconnect(self) -> None:
        self.dll.disconnect()

    def reset(self, mode: CubeProgrammerResetMode) -> None:
        status = self.dll.reset(mode)
        if status != 0:
            raise CubeProgrammerError(status)

    def connected(self) -> bool:
        return self.dll.checkDeviceConnection() == 1
    
    def start_fus(self) -> None:
        status = self.dll.startFus()
        if not status:
            raise CubeProgrammerError(status)

    @staticmethod
    def _init_progressbar() -> None:
        pass

    @staticmethod
    def _log_message(type, message) -> None:
        pass

    @staticmethod
    def _set_progessbar(current, total) -> None:
        pass
