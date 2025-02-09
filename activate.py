import subprocess
from dataclasses import dataclass, field
import json
import os
from concurrent.futures import ThreadPoolExecutor
from utils import timer
import pickle


@dataclass
class Enviroment:
    name: str = field(default="Unknown")
    packages: dict = field(init=False, default_factory=dict)
    size: str = field(init=False, default="Not Found")
    raw_package_list: str = field(init=False)
    reload: bool = field(init=False, default=False)


def hel():
    with ThreadPoolExecutor(max_workers=10) as exec:
        result = exec.map(package_list, env_list())
    for re in result:
        print(re)


@dataclass
class Conda:
    path: str = field(init=False, default="~/anaconda3/envs/")
    raw_list: list[str] = field(init=False, default=[])
    env_list: list[Enviroment] = field(init=False, default_factory=list)
    total_size: str = field(init=False, default="None")

    def __post_init__(self) -> None:
        self._path()
        self.get_env_list()

    def need_reload(self, obj):
        pass

    def _path(self) -> None:
        unsorted_path = os.path.join(os.environ["CONDA_PREFIX"], "envs")
        target_dir = "anaconda3/envs"
        idx = unsorted_path.find(target_dir)
        self.path = unsorted_path[: idx + len(target_dir)]

    def get_raw_list(self):
        self.raw_list = [
            i.name for i in os.scandir(self.path) if not i.name.startswith(".")
        ]

    def get_env_list(self) -> None:
        self.env_list = [
            Enviroment(name=i.name)
            for i in os.scandir(self.path)
            if not i.name.startswith(".")
        ]


def get_conda_instance() -> Conda:
    if os.path.exists("./pickle/conda_env_lis.pickle"):
        with open("./pickle/conda_env_lis.pickle", "rb") as file:
            loaded_conda = pickle.load(file)
        return loaded_conda
    else:
        return Conda()


def package_list(env: str) -> dict:
    env_path = f"/home/prince/anaconda3/envs/{env}/bin/python"  # Adjust for Windows
    cmd = [env_path, "-m", "pip", "list", "--format=json"]

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=True,
    )

    return {env: {i["name"]: i["version"] for i in json.loads(result.stdout)}}


@timer
def main() -> None:
    with ThreadPoolExecutor(max_workers=10) as exec:
        result = exec.map(package_list, env_list())
    for re in result:
        print(re)
