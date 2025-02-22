import asyncio
import os
from dataclasses import dataclass, field
from inotify.adapters import InotifyTree
from inotify.constants import IN_CREATE, IN_DELETE
from utils import logger
import threading


@dataclass
class DirectoryWatcher:
    path: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    seen: set = field(default_factory=set)

    async def watch(self):
        """Asynchronously listens for file creation and deletion events."""
        inotify = InotifyTree(self.path, mask=(IN_CREATE | IN_DELETE))
        loop = asyncio.get_running_loop()
        index = len(self.path.rstrip("/").split("/"))

        def process_events():
            """Detects events and puts unique values in the queue."""
            for event in inotify.event_gen(yield_nones=False):
                _, _, event_path, filename = event
                env_path = event_path.rstrip("/").split("/")
                if len(env_path) == index:
                    env = env_path[index - 1]
                elif len(env_path) > index:
                    env = env_path[index]
                else:
                    env = None

                if env and env not in self.seen:  # Check if value is unique
                    self.seen.add(env)  # Mark as seen
                    asyncio.run_coroutine_threadsafe(
                        self.queue.put(env), loop
                    )  # Put new value

        # Run `process_events()` in a background thread
        await loop.run_in_executor(None, process_events)

    async def process_events(self):
        """Processes exported unique values."""
        while True:
            env = await self.queue.get()
            logger.trace(f"Tracked : {env}")
            # Replace with any export logic


def start_watcher(dir_path: str):
    """Runs the async DirectoryWatcher in a separate thread."""
    path = os.path.expanduser(dir_path)
    watcher = DirectoryWatcher(path)

    async def run():
        """Runs the async watcher and event processor."""
        await watcher.watch()
        await watcher.process_events()

    # Start the event loop in a new thread
    thread = threading.Thread(target=lambda: asyncio.run(run()), daemon=True)
    thread.start()
    return watcher


async def main():
    """Runs the async file listener."""
    path = os.path.expanduser("~/anaconda3/envs/")
    watcher = DirectoryWatcher(path)

    # Start file watcher and event processor concurrently
    await asyncio.gather(watcher.watch(), watcher.process_events())


if __name__ == "__main__":
    asyncio.run(main())
