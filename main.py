import os
from utils import timer
import subprocess
from typing import List

# du -sh $("ls" ~/anaconda3/envs/)
home_path = os.environ.get("HOME") or ""
dir_path = os.path.join(home_path, "anaconda3/envs/")


def get_dir_size(list_of_dir: List[str]) -> List[str] | dict[str, str]:
    cmd = f"du -bs {' '.join(list_of_dir)} | awk '{{print $1}}'"
    try:
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, check=True
        )
        raw_size = result.stdout.splitlines()
        return raw_size
    except FileNotFoundError as e:
        return {"error": str(e)}  # Return error message in dictionary


@timer
def main():
    ls = [
        os.path.join(dir_path, i.name)
        for i in os.scandir(dir_path)
        if not i.name.startswith(".")
    ]

    out = get_dir_size(ls)
    for i in out:
        print(type(i))


if __name__ == "__main__":
    main()
