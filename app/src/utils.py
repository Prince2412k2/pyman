import time
import functools
import os

from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    format="<level>{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}</level>",
    level="TRACE",
    colorize=True,
    enqueue=True,
)


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        output = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken by {func.__name__} is {end-start} secs")
        return output

    return wrapper


home_path = os.environ.get("HOME", "~")
default_conda_path = os.path.expanduser(os.path.join(home_path, "anaconda3/envs"))
