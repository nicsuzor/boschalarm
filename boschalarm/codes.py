from enum import Enum, IntEnum

responses = {
    "00": "Non-specific error",
    "01": "Checksum failure (UDP connections only)",
    "02": "Invalid size / length",
    "03": "Invalid command",
    "04": "Invalid interface state",
    "05": "Data out of range",
    "06": "No authority",
    "07": "Unsupported command",
    "08": "Cannot Arm Area"
}


class areaStatus(IntEnum):
    unknown = 0
    allon = 1
    partoninstant = 2
    partondelay = 3
    disarmed = 4
    allonentrydelay = 5
    partonentrydelay = 6
    allonexitdelay = 7
    partonexitdelay = 8
    alloninstantarmed = 9


class BoschComands():
    ### Codes for commands, in HEX
    GET_PANEL_TIME = '18'
    WHATAREYOU = '01'
    PINCODE_CHECK = '3E'
    RESET_SENSORS = '18'
    REQUEST_TEXT_HISTORY = '16'
    REQUEST_HISTORY = '15'
    GET_REPORT_TEST = '1801'
    GET_REPORT = '1800'
    REQUEST_CAPACITIES = '1f'
    REQUEST_ALARM_PRIORITIES = '21'
    REQUEST_ALARM_AREAS = '22'
    GET_ALARM_MEMORY = '23'
    REQUEST_CONFIGURED_AREAS = '24'
    REQUEST_AREA_STATUS = '2600'  # 01'  # second byte is to request alarm reports if supported?
    ARM_AREAS = '27'
    REQUEST_AREAS_NOT_READY = '28'
    REQUEST_AREA_TEXT = '29'
    REQUEST_OUTPUTS = '30'
    REQUEST_OUTPUT_STATUS = '31'
    PANEL_STATE = '32'
    SET_OUTPUT_STATE = '32'
    REQUEST_OUTPUT_TEXT = '33'
    REQUEST_CONFIGURED_POINTS = '35'
    REQUEST_FAULTED_POINTS = '37'
    REQUEST_POINTS_IN_AREA = '36'
    REQUEST_POINT_STATUS = '38'
    REQUEST_CONFIGURED_DOORS = '2B'
    REQUEST_DOOR_STATUS = '2C'
    REQUEST_POINT_TEXT = '3C'
    SUBSCRIBE_ALL = '95 01 01 01 01 01 01 01 01 01'  # this definitely doesn't work yet
    REQUEST_SUBSCRIPTIONS = 'C6 01'
    SILENCE_ALARMS = '19'
    SOUND_ALARMS = '1A'


class Languages(IntEnum):
    English = 1


class ArmingType(IntEnum):
    Disarm = 1
    MasterInstantArm = 2
    MasterDelayArm = 3
    PerimeterInstantArm = 4
    PerimeterDelayArm = 5
    ForceAllOnDelay = 6
    ForceAllOnInstant = 7
    ForcePartOnDelay = 8
    ForcePartOnInstant = 9
    StayOneArm = 10
    StayTwoArm = 11
    AwayArm = 12
    ForceStayOneArm = 13
    ForceAwayArm = 15


class AlarmTypes(IntEnum):
    Unknown = 0
    BurglaryTrouble = 1
    BurglarySupervisory = 2
    GasTrouble = 3
    GasSupervisory = 4
    FireTrouble = 5
    FireSupervisory = 6
    BurglaryAlarm = 7
    PersonalEmergency = 8
    GasAlarm = 9
    FireAlarm = 10


class OutputCommands(IntEnum):
    Off = 0
    On = 1


class ResponseTypes(IntEnum):
    Ack = 252  # // 0x000000FC
    Nak = 253  # // 0x000000FD
    Data = 254  # // 0x000000FE


class ActionResults(IntEnum):
    NonSpecificError = 0
    ChecksumFailure = 1
    InvalidLengthSize = 2
    InvalidCommand = 3
    InvalidInterfaceState = 4
    DataOutOfRange = 5
    NoAuthority = 6
    UnsupportedCommand = 7
    CannotArmPanel = 8
    InvalidRemoteId = 9
    InvalidLicense = 10  # 0x0000000A
    InvalidMagicNumber = 11  # 0x0000000B
    NoRfDeviceWithThatRfid = 224  # 0x000000E0
    BadRfidNotProperFormat = 225  # 0x000000E1
    TooManyRfDevicesForPanel = 226  # 0x000000E2
    DuplicateRfid = 227  # 0x000000E3
    DuplicateAccessCard = 228  # 0x000000E4
    BadAccessCardData = 229  # 0x000000E5
    BadLanguageChoice = 230  # 0x000000E6
    BadSupervisionModeSelection = 231  # 0x000000E7
    BadEnableDisableChoice = 232  # 0x000000E8
    BadMonth = 233  # 0x000000E9
    BadDay = 234  # 0x000000EA
    BadHour = 235  # 0x000000EB
    BadMinute = 236  # 0x000000EC
    BadTimeEditChoice = 237  # 0x000000ED
    InvalidProductType = 240  # 0x000000F0
    UnsupportedPanelVersion = 241  # 0x000000F1
    SetupEncryptionFailed = 242  # 0x000000F2
    ProtocolLoginFailed = 243  # 0x000000F3
    UserLoginFailed = 244  # 0x000000F4
    InvalidProtocolIndicator = 245  # 0x000000F5
    OperationCancelled = 246  # 0x000000F6
    UnsupportedTransport = 247  # 0x000000F7
    TransportNotAllowed = 248  # 0x000000F8
    Timeout = 249  # 0x000000F9
    TransportConnectFailed = 250  # 0x000000FA
    TooManyConnections = 251  # 0x000000FB
    Success = 255  # 0x000000FF
