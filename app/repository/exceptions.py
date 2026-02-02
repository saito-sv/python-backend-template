"""Repository-level exceptions."""

import re

from sqlalchemy.exc import IntegrityError

# Regex which extracts the constraint name from a "unique constraint violation" error message.
_name_regex = r"violates unique constraint \"([^\"]+)\""


class DuplicateEntityException(Exception):
    """
    A duplicate entity exception is raised when the data store won't allow duplicate entities,
    but we either (1) just tried to add one or (2) updated an old row in such a way that we made one.

    We're currently backed by postgres, so this is basically a unique constraint violation.
    Repositories map those into this so that callers can catch them in a backend-agnostic way.
    """

    def __init__(self, cause: IntegrityError):
        """
        cause: The sqlalchemy error that the database actually threw.
        """
        message = str(cause)
        super().__init__(message)
        maybe_regex_match = re.search(_name_regex, message)
        self.constraint_violation_name = (
            "" if maybe_regex_match is None else maybe_regex_match.group(1)
        )
