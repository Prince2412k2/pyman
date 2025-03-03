from concurrent.futures import ThreadPoolExecutor
import subprocess
import json

from typing import Callable, Generator, Optional, Tuple, Set, List, Dict
from dataclasses import dataclass, field
import os

from utils import logger, default_conda_path, timer, cls
from watch import DirectoryWatcher
import asyncio


@dataclass
class GetThreads:
    @staticmethod
    def thread_pool(list_items: list, func: Callable) -> list:
        logger.debug(f"ThreadPool Started for {len(list_items)} processes")
        with ThreadPoolExecutor() as exec:
            result = list(exec.map(func, list_items))
        logger.debug("ThreadPool Finished")
        return result


def subprocess_call(cmd) -> str | dict:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, check=True
        )
        stdout_raw = result.stdout
        return stdout_raw
    except Exception as e:
        return {"error": str(e)}


def byte_to_string(size: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.{2}f} {units[i]}"


@dataclass(eq=True, unsafe_hash=True)
class Environment:
    name: str
    path: str
    packages: dict = field(init=False, default_factory=dict)
    file_num: int = field(init=False)
    size: Tuple[float, str] = field(init=False, default=(0.0, "0 bytes"))

    def __post_init__(self):
        if not os.path.exists(self.path):
            logger.error(f"The path env_path='{self.path}' Doest exist")
        else:
            logger.info(f"path to env is set at '{self.path}'")
            self.file_num = self.fetch_file_num()
            # self.size = self.fetch_size()

    def get_packages(self) -> Optional[Dict[str, str]]:
        python_path = os.path.join(self.path, "bin/python")
        logger.debug(python_path)
        cmd = [
            python_path,
            "-m",
            "pip",
            "list",
            "--format=json",
        ]
        try:
            result = subprocess_call(cmd)
            if isinstance(result, str):
                return {i["name"]: i["version"] for i in json.loads(result)}
            else:
                logger.error("subprocess_call failed")
                return None
        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            FileNotFoundError,
        ) as e:
            return {"error": str(e)}

    def fetch_file_num(self) -> int:
        """Returns the total number of files in a directory."""
        return sum(1 for _ in self.iter_files(self.path))

    def has_changed(self, updated_file_num: int) -> bool:
        return self.file_num != updated_file_num

    def reload(self, packages: dict, file_num: int, size: Tuple[float, str]):
        self.packages = packages
        self.file_num = file_num
        self.size = size

    @staticmethod
    def iter_files(directory: str) -> Generator[os.DirEntry, None, None]:
        """Yields file entries from a directory recursively using a stack."""
        stack = [directory]
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if entry.is_file(follow_symlinks=False):
                            yield entry  # Yield file entry
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)  # Add subdirectory to stack
            except PermissionError:
                pass


@dataclass
class Conda:
    path: str = field(init=False)
    environments: Dict[str, Environment] = field(init=False)
    reload_pool: set = field(init=False)

    def __post_init__(self):
        self.path = self.fetch_path()

    def initialize(self):
        self.environments = self.set_environments()
        # logger.debug("envs are set")
        all_size = self.fetch_size(list(self.environments.keys()))
        self.set_environments_size(all_size)
        return self

    def fetch_path(self) -> str:
        if os.environ.get("CONDA_PREFIX"):
            unsorted_path = os.path.join(os.environ["CONDA_PREFIX"], "envs")
            target_dir = "anaconda3/envs"
            idx = unsorted_path.find(target_dir)
            sorted_path = unsorted_path[: idx + len(target_dir)]
            logger.debug(f"Found conda path at : '{sorted_path}'")
            return sorted_path
        else:
            logger.warning(
                "Path To Conda Env Not Found (Using Default : '~/anaconda3/envs/') else set it manually"
            )
            return default_conda_path

    def set_environments(self):
        return {
            i.name: Environment(i.name, os.path.join(self.path, i.name))
            for i in os.scandir(self.path)
            if not i.name.startswith(".")
        }

    def fetch_size(self, list_of_dir: List[str]) -> dict[str, float | str]:
        """Returns the total size (in bytes) of all files in a directory."""

        logger.debug(f"getting sizes for : '{len(list_of_dir)}' envs")

        paths_to_dir = [os.path.join(self.path, i) for i in list_of_dir]
        cmd = f"du -bs {' '.join(paths_to_dir)} | awk '{{print $1}}'"
        try:
            result = subprocess.run(
                cmd, shell=True, text=True, capture_output=True, check=True
            )
            raw_size = result.stdout.splitlines()
            logger.debug(f"got sizes : '{len(raw_size)}' envs")
            return {
                name: float(temp_size) for name, temp_size in zip(list_of_dir, raw_size)
            }

        except FileNotFoundError as e:
            return {"error": str(e)}

    def set_environments_size(self, dict_size: dict[str, float]):
        for key, val in dict_size.items():
            self.environments[key].size = (val, byte_to_string(val))


async def main():
    conda = Conda()
    conda.initialize()  # Ensure initialization is correct

    watcher = DirectoryWatcher(conda.path)
    asyncio.create_task(watcher.watch())  # Run watcher asynchronously

    while True:
        if await watcher.check_for_changes():  # Wait for a change
            cls()
            conda.initialize()  # Re-initialize Conda (reload environments)

            for env in conda.environments:
                logger.warning(env)  # Log environment changes


if __name__ == "__main__":
    asyncio.run(main())
