"""The one error type every email sender raises, so callers don't care which service is used."""


class EmailError(Exception):
    pass
