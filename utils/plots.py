import asyncio
from datetime import datetime
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.dates import ConciseDateFormatter


async def draw_moods_plot(data: tuple[np.ndarray[datetime], np.ndarray[int]]) -> BytesIO:
    return await asyncio.get_event_loop().run_in_executor(None, __draw_moods_plot, data)


def __draw_moods_plot(data: tuple[np.ndarray[datetime], np.ndarray[int]]) -> BytesIO:
    ax: Axes
    _, ax = plt.subplots()
    ax.xaxis.set_major_formatter(ConciseDateFormatter(ax.xaxis.get_major_locator()))
    plt.title("Your moods")
    plt.grid(color="grey", linestyle="--", linewidth=0.3)
    plt.plot(*data, "g-")

    io = BytesIO()
    plt.savefig(io, format="png")
    io.seek(0)
    return io
