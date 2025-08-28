class AwesomeListError(Exception):
    """Base exception for awesome list processing errors."""

    pass


class MarkdownParseError(AwesomeListError):
    """Exception raised when markdown parsing fails."""

    def __init__(self, message: str, file_path: str = "", line_number: int = 0):
        self.file_path = file_path
        self.line_number = line_number

        if file_path and line_number:
            full_message = f"{message} (file: {file_path}, line: {line_number})"
        elif file_path:
            full_message = f"{message} (file: {file_path})"
        else:
            full_message = message

        super().__init__(full_message)


class TagInheritanceError(AwesomeListError):
    """Exception raised when tag inheritance processing fails."""

    pass


class CacheGenerationError(AwesomeListError):
    """Exception raised when cache generation fails."""

    def __init__(self, message: str, source_files: list[str] | None = None):
        self.source_files = source_files if source_files is not None else []

        if source_files:
            full_message = f"{message} (sources: {', '.join(source_files)})"
        else:
            full_message = message

        super().__init__(full_message)


class InvalidAwesomeListError(MarkdownParseError):
    """Exception raised when awesome list format is invalid."""

    pass
