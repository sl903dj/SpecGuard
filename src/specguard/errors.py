class SpecGuardError(Exception):
    """Base error for expected review failures."""


class ConfigError(SpecGuardError):
    """Invalid configuration. Exit 4, before checks."""


class UsageError(SpecGuardError):
    """The review cannot start. Exit 4, before or instead of a clean result."""


class ReadOnlyError(SpecGuardError):
    """A mutating Git command was refused."""


class StatusRewriteError(SpecGuardError):
    """A non-passing check status was rewritten as PASS."""


class ProviderError(SpecGuardError):
    """The configured model provider failed or was misused."""
