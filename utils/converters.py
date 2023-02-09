import disnake
import pendulum
from disnake.ext import commands

from utils.errors import DateConversionFailure

utc = pendulum.timezone("utc")


class DateConverter(commands.Converter, pendulum.Date):
    @commands.converter_method
    async def convert(self, inter: disnake.ApplicationCommandInteraction, argument: str) -> pendulum.Date:
        try:
            d = utc.convert(pendulum.parse(argument, strict=False))
            if isinstance(d, pendulum.DateTime):
                return pendulum.Date.fromtimestamp(d.timestamp())
            if isinstance(d, pendulum.Date):
                return d
            raise DateConversionFailure()
        except Exception:
            raise DateConversionFailure()
