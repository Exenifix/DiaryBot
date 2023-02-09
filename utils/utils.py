import asyncio
from io import BytesIO


async def generate_diary(data: dict[str, str]) -> BytesIO:
    return await asyncio.get_event_loop().run_in_executor(None, __generate_diary, data)


def __generate_diary(data: dict[str, str]) -> BytesIO:
    txt = ""
    for date, content in data.items():
        txt += f"{date}\n{'=' * 30}\n{content}\n\n"

    io = BytesIO()
    io.write(txt.encode())
    io.seek(0)
    return io
