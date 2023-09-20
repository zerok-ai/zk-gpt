from enum import Enum


class EventType(Enum):
    QNA = 'QNA'
    USER_ADDITION = 'USER_ADDITION'
    INFERENCE = 'INFERENCE'
    TRACE_SWITCH = 'TRACE_SWITCH'
