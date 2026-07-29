class PDFImageToolkitError(Exception):
    """Base exception for friendly application errors."""


class InvalidFileError(PDFImageToolkitError):
    """Raised when a selected file is invalid or unsupported."""


class ConversionError(PDFImageToolkitError):
    """Raised when conversion fails."""


class UserInputError(PDFImageToolkitError):
    """Raised when user input is missing or invalid."""