from conda import Conda
from .logger import logger

conda = Conda()
environments = conda.environments


def test_conda_path():
    assert conda.path == "/home/prince/anaconda3/envs"


def test_conda_env_obj():
    ls = conda.environments
    assert len(ls) == 8
    assert (
        list(ls.keys()).sort()
        == [
            "asci",
            "book",
            "Chatbot",
            "my_env",
            "pyman",
            "roid",
            "test",
            "yapp",
        ].sort()
    )


def test_fetch_sizes():
    lsdir = list(conda.environments.keys())

    sizes = list(conda.fetch_size(lsdir).values())
    assert type(sizes) is list

    if isinstance(sizes, list):
        assert (
            sizes.sort()
            == [
                474126572.0,
                2129476607.0,
                590644196.0,
                136951377.0,
                707532670.0,
                216058880.0,
                1412758050.0,
                1422610985.0,
            ].sort()
        )


def test_Evironment_path():
    assert environments["pyman"].path == "/home/prince/anaconda3/envs/pyman"


def test_Evironment_get_packages():
    pyman_packages = {
        "camelcase": "0.2",
        "mkl_fft": "1.3.11",
        "mkl_random": "1.2.8",
        "mkl-service": "2.4.0",
        "numpy": "2.2.2",
        "opencv-python": "4.10.0",
        "opencv-python-headless": "4.10.0",
        "pip": "24.2",
        "setuptools": "72.1.0",
        "wheel": "0.44.0",
    }
    env_packages = environments["test"].get_packages()
    assert env_packages is not None
    assert list(env_packages.keys()).sort() == list(pyman_packages.keys()).sort()
    assert list(env_packages.values()).sort() == list(pyman_packages.values()).sort()


def test_Evironment_fetch_file_num():
    env = environments["test"]
    num = env.fetch_file_num()
    assert num == 27352


def test_Evironment_has_changed():
    env = environments["test"]
    right_num = 27352
    wrong_num = 27354

    assert not env.has_changed(right_num)
    assert env.has_changed(wrong_num)


def test_Evironment_set_environment_size():
    lsdir = list(conda.environments.keys())
    size = conda.fetch_size(lsdir)
    conda.set_environments_size(size)
    for size, (name, env) in zip(size, conda.environments.items()):
        assert env.size == size
