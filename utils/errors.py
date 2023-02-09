import inspect
import sys

from disnake import Forbidden, NotFound
from disnake.ext import commands


class _Unknown:
    pass


UNKNOWN = _Unknown()


class CustomException(commands.CommandError):
    pass


class EntryAlreadyExists(CustomException):
    def __init__(self):
        super().__init__("Entry on this day already exists. Use `/edit_entry` to edit it.")


class DateConversionFailure(CustomException):
    def __init__(self):
        super().__init__("Invalid date format. Correct ones are: `Jan 11`, `March 20 2023`")


known_exceptions = [
    i[1]
    for i in inspect.getmembers(sys.modules[__name__], lambda x: inspect.isclass(x) and issubclass(x, CustomException))
]

known_exceptions.extend(
    [
        commands.MissingRequiredArgument,
        commands.ArgumentParsingError,
        commands.BadArgument,
        commands.CheckFailure,
        commands.CommandNotFound,
        commands.DisabledCommand,
        commands.CommandOnCooldown,
        commands.NotOwner,
        commands.MemberNotFound,
        commands.UserNotFound,
        commands.ChannelNotFound,
        commands.RoleNotFound,
        commands.MissingPermissions,
        commands.BotMissingPermissions,
        commands.MissingRole,
        commands.MissingAnyRole,
        NotFound,
        Forbidden,
    ]
)


def get_error_msg(error: commands.CommandError):
    error = getattr(error, "original", error)
    if type(error) not in known_exceptions:
        return UNKNOWN

    return str(error)
