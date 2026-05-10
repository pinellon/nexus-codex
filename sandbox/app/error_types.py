"""Tipos de erro do NEXUS."""

from enum import Enum


class ErrorCode(Enum):
    APP_NOT_FOUND = "APP_NOT_FOUND"
    INVALID_COMMAND = "INVALID_COMMAND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    OPENAI_ERROR = "OPENAI_ERROR"
    VOICE_ERROR = "VOICE_ERROR"
    FILE_ERROR = "FILE_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    BROWSER_ERROR = "BROWSER_ERROR"
    MEDIA_ERROR = "MEDIA_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class NexusError(Exception):
    def __init__(self, code: ErrorCode, user_message: str, technical_message: str = ""):
        self.code = code
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        super().__init__(self.user_message)

