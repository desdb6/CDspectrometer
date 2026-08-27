import ctypes
from ctypes import c_short, c_long, c_double, c_char_p, c_int, POINTER, c_bool

class SPdbUSBm:
    def __init__(self, dll_path):
        # WinDLL uses the __stdcall calling convention, which this DLL's
        # functions use (matches its VB6-era @N decorated exports).
        # This also works correctly on 64-bit, where stdcall/cdecl are
        # not distinguished, so WinDLL is safe for both DLL builds.
        self.dll = ctypes.WinDLL(dll_path)
        self._setup_functions()

    def _bind(self, plain_name, decorated_name, argtypes, restype):
        """Look up a DLL function by its plain name, falling back to a
        decorated (stdcall @N) export name if the plain name isn't
        exported. Some DLL builds only export certain functions in
        decorated form. Caches the result under the plain attribute
        name on self.dll so later self.dll.<plain_name>(...) calls
        keep working normally."""
        try:
            func = getattr(self.dll, plain_name)
        except AttributeError:
            func = self.dll[decorated_name]
            setattr(self.dll, plain_name, func)
        func.argtypes = argtypes
        func.restype = restype
        return func

    def _setup_functions(self):
        self.dll.spTestAllChannels.argtypes = [c_short]
        self.dll.spTestAllChannels.restype = c_short

        self.dll.spSetupAllChannels.argtypes = []
        self.dll.spSetupAllChannels.restype = c_short

        self.dll.spSetupGivenChannel.argtypes = [c_short]
        self.dll.spSetupGivenChannel.restype = c_short

        self.dll.spInitAllChannels.argtypes = [c_short]
        self.dll.spInitAllChannels.restype = c_short

        self.dll.spInitGivenChannel.argtypes = [c_short, c_short]
        self.dll.spInitGivenChannel.restype = c_short

        self.dll.spSetIntEx.argtypes = [c_long, c_short]
        self.dll.spSetIntEx.restype = c_short

        self.dll.spSetDblIntEx.argtypes = [c_long, c_short]
        self.dll.spSetDblIntEx.restype = c_short

        self.dll.spSetTrgEx.argtypes = [c_short, c_short]
        self.dll.spSetTrgEx.restype = c_short

        self.dll.spReadDataEx.argtypes = [POINTER(c_long), c_short]
        self.dll.spReadDataEx.restype = c_short

        self.dll.spCloseAllChannels.argtypes = []
        self.dll.spCloseAllChannels.restype = c_short

        self.dll.spCloseGivenChannel.argtypes = [c_short]
        self.dll.spCloseGivenChannel.restype = c_short

        self.dll.spWriteChannelID.argtypes = [c_short, c_short]
        self.dll.spWriteChannelID.restype = c_short

        self.dll.spReadChannelID.argtypes = [POINTER(c_short), c_short]
        self.dll.spReadChannelID.restype = c_short

        self.dll.spGetAssignedChannelID.argtypes = [POINTER(c_short)]
        self.dll.spGetAssignedChannelID.restype = None

        self.dll.spPolyCalc.argtypes = [POINTER(c_double), c_short, c_double, POINTER(c_double)]
        self.dll.spPolyCalc.restype = None

        self.dll.spPolyFit.argtypes = [POINTER(c_double), POINTER(c_double), c_short, POINTER(c_double), c_short]
        self.dll.spPolyFit.restype = c_short

        self.dll.spSetIntMode.argtypes = [c_short, c_double, c_short]
        self.dll.spSetIntMode.restype = c_short

        self.dll.spSetExtEdgeMode.argtypes = [c_short, c_short]
        self.dll.spSetExtEdgeMode.restype = c_short

        self.dll.spCheckSpeedMode.argtypes = [POINTER(c_int), c_short]
        self.dll.spCheckSpeedMode.restype = c_short

        self.dll.spGetDevIsNew.argtypes = [c_short]
        self.dll.spGetDevIsNew.restype = c_short

        self.dll.spDevInfo.argtypes = [c_char_p, c_char_p, c_short]
        self.dll.spDevInfo.restype = c_short

        self.dll.spGetWLTable.argtypes = [POINTER(c_double), c_short]
        self.dll.spGetWLTable.restype = c_short

        self.dll.spDupdate.argtypes = [c_int, c_int, c_short]
        self.dll.spDupdate.restype = c_short

        self.dll.spReadDataExT.argtypes = [POINTER(c_long), c_short]
        self.dll.spReadDataExT.restype = c_short

        self.dll.spReadDark.argtypes = [POINTER(c_int), c_int, c_short]
        self.dll.spReadDark.restype = c_short

        self._bind("spSetOffsetCorrection", "_spSetOffsetCorrection@8",
                   [c_bool, c_short], c_short)

        self.dll.spSetBaseLineCorrection.argtypes = [c_bool, c_short, c_double, c_short]
        self.dll.spSetBaseLineCorrection.restype = c_short

        self.dll.spSetShutterPos.argtypes = [c_short, c_short]
        self.dll.spSetShutterPos.restype = c_short

        self.dll.spInsShutter.argtypes = [c_short]
        self.dll.spInsShutter.restype = c_short

        self.dll.spGetShutterPos.argtypes = [c_short]
        self.dll.spGetShutterPos.restype = c_short

    def spTestAllChannels(self, param):
        return self.dll.spTestAllChannels(param)

    def spSetupAllChannels(self):
        return self.dll.spSetupAllChannels()

    def spSetupGivenChannel(self, param):
        return self.dll.spSetupGivenChannel(param)

    def spInitAllChannels(self, param):
        return self.dll.spInitAllChannels(param)

    def spInitGivenChannel(self, param1, param2):
        return self.dll.spInitGivenChannel(param1, param2)

    def spSetIntEx(self, param1, param2):
        return self.dll.spSetIntEx(param1, param2)

    def spSetDblIntEx(self, param1, param2):
        return self.dll.spSetDblIntEx(param1, param2)

    def spSetTrgEx(self, param1, param2):
        return self.dll.spSetTrgEx(param1, param2)

    def spReadDataEx(self, param1, param2):
        return self.dll.spReadDataEx(param1, param2)

    def spCloseAllChannels(self):
        return self.dll.spCloseAllChannels()

    def spCloseGivenChannel(self, param):
        return self.dll.spCloseGivenChannel(param)

    def spWriteChannelID(self, param1, param2):
        return self.dll.spWriteChannelID(param1, param2)

    def spReadChannelID(self, param1, param2):
        return self.dll.spReadChannelID(param1, param2)

    def spGetAssignedChannelID(self, param):
        self.dll.spGetAssignedChannelID(param)

    def spPolyCalc(self, param1, param2, param3, param4):
        self.dll.spPolyCalc(param1, param2, param3, param4)

    def spPolyFit(self, param1, param2, param3, param4, param5):
        return self.dll.spPolyFit(param1, param2, param3, param4, param5)

    def spSetIntMode(self, param1, param2, param3):
        return self.dll.spSetIntMode(param1, param2, param3)

    def spSetExtEdgeMode(self, param1, param2):
        return self.dll.spSetExtEdgeMode(param1, param2)

    def spCheckSpeedMode(self, param1, param2):
        return self.dll.spCheckSpeedMode(param1, param2)

    def spGetDevIsNew(self, param):
        return self.dll.spGetDevIsNew(param)

    def spDevInfo(self, param1, param2, param3):
        return self.dll.spDevInfo(param1, param2, param3)

    def spGetWLTable(self, param1, param2):
        return self.dll.spGetWLTable(param1, param2)

    def spDupdate(self, param1, param2, param3):
        return self.dll.spDupdate(param1, param2, param3)

    def spReadDataExT(self, param1, param2):
        return self.dll.spReadDataExT(param1, param2)

    def spReadDark(self, param1, param2, param3):
        return self.dll.spReadDark(param1, param2, param3)

    def spSetOffsetCorrection(self, param1, param2):
        return self.dll.spSetOffsetCorrection(param1, param2)

    def spSetBaseLineCorrection(self, param1, param2, param3, param4):
        return self.dll.spSetBaseLineCorrection(param1, param2, param3, param4)

    def spShutter(self, param1, param2):
        return self.dll.spSetShutterPos(param1, param2)

    def spIntShutter(self, param1):
        return self.dll.spInsShutter(param1)

    def spGetShutter(self, param1):
        return self.dll.spGetShutterPos(param1)
