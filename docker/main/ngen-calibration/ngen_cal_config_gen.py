import argparse
import yaml
import os
from pathlib import Path
from typing import Union


def _handle_args():
    # get the command line parser
    parser = argparse.ArgumentParser(description='Generate a correct, adjusted ngen-cal config from an initial one.')
    parser.add_argument('config_file', type=Path, help='The external, base configuration yaml file.')
    return parser.parse_args()


def _adjust_config_file_path(old_path: Union[Path, str], new_parent_dir: Path) -> Path:
    if isinstance(old_path, str):
        old_path = Path(old_path)
    return new_parent_dir.joinpath(old_path.name)


def _set_num_proc(model_config_yaml: dict):
    """
    Make sure the ``parallel`` sub-element of the ``model`` element in the generated config is validly set.

    The ``NGEN_NUM_PROC`` environment variable will be written to this element if the former is present (regardless of
    whether the value is valid).  Otherwise, the already present value (or lack thereof) is considered in the next step.

    After checking for a value from the environment, the ``parallel`` value within the passed-in dictionary is sanity-
    checked.  If it isn't present, this raises an exception.  If it isn't less than 2, this also raise an exception.

    Parameters
    ----------
    model_config_yaml : dict
        The dictionary present at the ``model`` key within the initial base YAML config.
    """
    config_key = 'parallel'
    # Force value from env var to be used if env variable is present, even if it's invalid and forces us to bail
    if 'NGEN_NUM_PROC' in os.environ:
        try:
            model_config_yaml[config_key] = int(os.environ['NGEN_NUM_PROC'])
        except TypeError as e:
            raise RuntimeError("Can't generate calibration config with non-numeric number of parallel processes")
    # Once here, we have whatever we are going forward with, so sanity check it
    if config_key not in model_config_yaml or model_config_yaml[config_key] is None:
        raise RuntimeError("Can't generate calibration config without being provided number of parallel processors")
    elif model_config_yaml[config_key] < 2:
        raise ValueError("Can't generate calibration config with less than 2 parallel processes set")


def main():
    """
    Generate an appropriate config file based on a given config, tweaking and sanity checking where needed.
    """
    args = _handle_args()

    with open(args.config_file) as file:
        config = yaml.safe_load(file)

    model_config = config['model']

    # Apply the ngen binary setting appropriately based on environment variable
    model_config['binary'] = os.getenv('NGEN_BINARY', 'ngen')

    # Set the parallelization CPU/process count
    _set_num_proc(model_config)

    # Override 'strategy' if set in env (should be one of uniform, independent, explicit; however, not checked here)
    if 'NGEN_CAL_STRATEGY' in os.environ:
        model_config['strategy'] = os.environ['NGEN_CAL_STRATEGY']

    # Statically set the location of the configs coming via datasets
    model_config['partitions'] = Path(os.environ['PARTITION_DATASET_DIR']).joinpath('partition_config.json')
    model_config['realization'] = Path(os.environ['REALIZATION_CONFIG_DATASET_DIR']).joinpath('realization_config.json')
    hydrofabric_dataset_dir = Path(os.environ['HYDROFABRIC_DATASET_DIR'])
    model_config['catchments'] = hydrofabric_dataset_dir.joinpath('catchment_data.geojson')
    model_config['nexus'] = hydrofabric_dataset_dir.joinpath('nexus_data.geojson')
    model_config['crosswalk'] = hydrofabric_dataset_dir.joinpath('crosswalk.json')


if __name__ == "__main__":
    main()
