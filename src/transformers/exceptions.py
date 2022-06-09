from typing import List, Tuple, Union


class ValidationError(Exception):
    """Data is invalid. Multiple reasons can be given."""

    def __init__(self, *reasons: Union[str, List[str], Tuple[str]]):
        """
        Initialize the error with one or more reasons.

        Args:
            reasons: The reason(s) for this error.
        """
        if len(reasons) == 1 and isinstance(reasons[0], (list, tuple)):
            reasons = tuple(reasons[0])

        self.reasons = reasons
        """The reason(s) for this error."""

    @property
    def args(self):  # type: ignore[no-untyped-def]
        """
        The reason(s) for this error.

        This is for repr-ification and compatibility with other exceptions, especially in testing.

        Returns:
            The reason(s) for this error.
        """
        return self.reasons

    def __str__(self) -> str:
        """
        A string representing the reason(s) for this error.

        If only one reason is given, use it. Otherwise, stringify the tuple of reasons.

        Returns:
            A string representing the reason(s) for this error.
        """
        return str(self.reasons)


class ContentValidationError(ValidationError):
    """Data is in the correct format but is otherwise invalid."""
