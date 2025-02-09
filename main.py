import os
import subprocess

conda_prefix = str(os.environ.get("CONDA_PREFIX_1"))
current_env = os.path.basename(str(os.environ.get("CONDA_PREFIX")))
env_path = os.path.join(conda_prefix, "envs")
subprocess.run(
    ". /home/prince/anaconda3/envs/pyman/etc/profile.d/conda.sh ; ",
    shell=True,
    executable="/bin/bash",
)

# activated_env = os.path.basename(path)
conda_enviroment_list = [
    i.name for i in os.scandir(env_path) if not i.name.startswith(".")
]
for i in conda_enviroment_list:
    if i == current_env:
        print("* ", end="")
    else:
        print("  ", end="")
    print(i)
