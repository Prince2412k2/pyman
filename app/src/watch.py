import asyncio
from dataclasses import dataclass, field
from inotify.adapters import InotifyTree
from inotify.constants import IN_CREATE, IN_DELETE
from loguru import logger


@dataclass
class DirectoryWatcher:
    path: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    seen: set = field(default_factory=set)
    debounce_time: float = 3.0  # Time to wait before processing batch

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

                env = env_path[index] if len(env_path) > index else env_path[index - 1]

                logger.debug(f"Detected change in env: {env}")
                if env and env not in self.seen:
                    self.seen.add(env)
                    asyncio.run_coroutine_threadsafe(self.queue.put(env), loop)

        await loop.run_in_executor(None, process_events)

    async def check_for_changes(self):
        """Waits until at least one change is detected, then returns the batch."""
        while True:
            await self.queue.get()  # Wait for the first change
            await asyncio.sleep(self.debounce_time)  # Wait to debounce

            changes = list(self.seen)
            self.seen.clear()
            return changes  # Return all detected changes as a batch

    async def empty(self):
        self.seen.clear()


async def main():
    watcher = DirectoryWatcher("/home/prince/anaconda3/envs")
    asyncio.create_task(watcher.watch())

    while True:
        changes = await watcher.check_for_changes()
        logger.warning(f"Changes detected: {changes}")


# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())
