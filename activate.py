import subprocess
from dataclasses import dataclass, field
import json
import os
from concurrent.futures import ThreadPoolExecutor
from utils import timer
import pickle
from vars import default_conda_path
from typing import Dict, List, Tuple, Union
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


class Utils:
    @staticmethod
    def byte_to_string(size: float) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.{2}f} {units[i]}"


@dataclass
class Environment:
    name: str = field(default="Unknown")
    path: str = field(init=False)
    packages: Dict[str, str] = field(init=False, default_factory=dict)
    size: str = field(init=False, default="Not Found")
    raw_package_list: str = field(init=False)


@dataclass
class Conda(Utils):
    conda_path: str = field(init=False, default="~/anaconda3/envs/")
    env_names: List[str] = field(init=False)
    env_obj_list: List[Environment] = field(init=False, default_factory=list)
    size_all: str = field(init=False, default="Unknown")

    def __post_init__(self) -> None:
        self._set_conda_path()
        logger.trace("Set conda_path")
        self.env_names = self.get_env_name()
        logger.trace("Set env_names")
        self._reload_env()
        self.set_env_path()
        logger.trace("Set env_paths")
        self.set_env_size()
        logger.trace("Set env_size")

    def _set_conda_path(self) -> None:
        if os.environ.get("CONDA_PREFIX"):
            unsorted_path = os.path.join(os.environ["CONDA_PREFIX"], "envs")
            target_dir = "anaconda3/envs"
            idx = unsorted_path.find(target_dir)
            self.conda_path = unsorted_path[: idx + len(target_dir)]
            logger.info(f"Found conda path at {self.conda_path}")
        else:
            logger.warning(
                "PATH TO CONDA ENV NOT FOUND SET IT MANUALLY, by default it will use ~/anaconda3/envs/"
            )
            self.conda_path = default_conda_path

    def get_env_name(self) -> List[str]:
        return [
            i.name for i in os.scandir(self.conda_path) if not i.name.startswith(".")
        ]

    def set_env_path(self) -> None:
        for i in self.env_obj_list:
            i.path = os.path.join(self.conda_path, i.name)

    def get_dir_size(self) -> Tuple[bool, Union[List[float], str]]:
        cmd = f"du -bs {' '.join([i.path for i in self.env_obj_list])} | awk '{{print $1}}'"
        try:
            result = subprocess.run(
                cmd, shell=True, text=True, capture_output=True, check=True
            )
            raw_size = result.stdout.splitlines()
            return False, list(map(float, raw_size))  # Success case
        except subprocess.CalledProcessError as e:
            return True, f"Error in subprocess: {e}"  # Error case

    def set_env_size(self):
        err, sizes = self.get_dir_size()
        if not err:
            for obj, vol in zip(self.env_obj_list, sizes):
                obj.size = self.byte_to_string(vol)
            self.size_all = self.byte_to_string(sum(sizes))

    def set_env_obj(self) -> None:
        self.env_obj_list = [Environment(i) for i in self.env_names]

    def _reload_env(self) -> None:
        self.set_env_obj()
        logger.trace("set env obj")
        self.thread_loop()
        logger.trace("runnin thread loop")
        # self.set_env_size()

    def reload(self, force_reload=False):
        updated_list = self.get_env_name()
        if self.env_names == updated_list and not force_reload:
            return False
        else:
            self.env_names = updated_list
            self._reload_env()
            return True

    def thread_loop(
        self,
    ) -> List[Dict]:
        logger.debug(f"ThreadPool Started for {len(self.env_names)} processes")

        with ThreadPoolExecutor() as exec:
            result = list(exec.map(self.get_packages, self.env_names))

        for obj, stdout_list in zip(self.env_obj_list, result):
            obj.packages = stdout_list
            logger.debug(f"Retrieved packages for environment: {obj.name}")
        return result

    def get_packages(self, env: str) -> Dict[str, str]:
        env_path = f"{self.conda_path}/{env}/bin/python"  # Adjust for Windows

        if not os.path.exists(env_path):
            logger.error(f"The path env_path='{env_path}' Doest exist")

        cmd = [env_path, "-m", "pip", "list", "--format=json"]
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=True)
            return {i["name"]: i["version"] for i in json.loads(result.stdout)}

        except (
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            FileNotFoundError,
        ) as e:
            return {"error": str(e)}  # Return error message in dictionary

    def get_env_list_out(self) -> None:
        for i in self.env_obj_list:
            print(50 * "-" + f"{i.name}" + 50 * "-", end="\n")

    def save_state(self) -> None:
        os.makedirs("./pickle", exist_ok=True)
        with open("./pickle/conda.pkl", "wb") as file:
            pickle.dump(self, file)

    def get_total_size(self):
        return self.size_all

    def all_env_size_out(self):
        for i in self.env_obj_list:
            print(f"{i.name}:{i.size}")


def get_conda_instance() -> Conda:
    if os.path.exists("./pickle/cona.pkl"):
        with open("./pickle/conda.pkl", "rb") as file:
            loaded_conda = pickle.load(file)
            logger.info("Using the pkl file")
        return loaded_conda
    else:
        logger.info("Using a new instance")
        return Conda()


@timer
def main() -> None:
    ins = get_conda_instance()

    ins.reload()
    ins.save_state()
    ins.all_env_size_out()


if __name__ == "__main__":
    main()
