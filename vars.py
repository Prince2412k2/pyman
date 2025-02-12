import os

home_path = os.environ.get("HOME", "~")  # Use ~ if HOME is missing
default_conda_path = os.path.expanduser(os.path.join(home_path, "anaconda3/envs"))
