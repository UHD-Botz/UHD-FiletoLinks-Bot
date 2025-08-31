class FileNotFound(Exception):
    """Raised when the requested file is not found"""
    pass

class InvalidFileID(Exception):
    """Raised when a file ID is invalid"""
    pass

class UnauthorizedAccess(Exception):
    """Raised when user tries to access without permission"""
    pass
