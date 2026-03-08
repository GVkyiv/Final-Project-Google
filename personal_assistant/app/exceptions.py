class PersonalAssistantError(Exception):
    """Base exception for Personal Assistant."""
    pass


class ValidationError(PersonalAssistantError):
    """Raised when data validation fails."""
    pass


class NotFoundError(PersonalAssistantError):
    """Raised when a requested resource is not found."""
    pass


class StorageError(PersonalAssistantError):
    """Raised when reading or writing data fails."""
    pass
