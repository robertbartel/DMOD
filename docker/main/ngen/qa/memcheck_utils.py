import argparse
import subprocess
import logging

from pathlib import Path
from typing import Tuple, Union

# Hopefully this ends up being worth the trouble
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# TODO: (later) perhaps an option to control this
#logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

EX_CFGS_DIR: Path = Path("/dmod/qa/realization_configs")
""" Path : Parent directory for realization configs to use with memcheck. """

# TODO: look at improving how paths are handled here
EXAMPLE_CATCHMENT_FILE= "/dmod/datasets/hydrofabric/ex_geojson_hf_01/catchment_data.geojson"
EXAMPLE_NEXUS_FILE= "/dmod/datasets/hydrofabric/ex_geojson_hf_01/nexus_data.geojson"

# TODO: make sure path to executable is set properly if we mess with paths
NGEN_PATH="/ngen/ngen/cmake_build/ngen"

OUTPUT_BASE_DIR = Path("/dmod/datasets/output")


def run_valgrind(realization_config: Path, catchment_file: Path, nexus_file: Path, skip_command_check: bool = False,
                 catchments: Tuple[str] = tuple(), nexuses: Tuple[str] = tuple()):
    """
    Run valgrind memcheck on ngen with the provided configuration details

    Parameters
    ----------
    realization_config : Path
        Realization config to use for ngen.
    catchment_file : Path
        The catchment hydrofabric file to use for ngen.
    nexus_file : Path
        The nexus hydrofabric file to use for ngen
    skip_command_check : bool
        If ``True`` (``False`` is the default), skip a check that ngen will actually run successfully with this config.
    catchments : Tuple[str]
        Collection of catchment string ids to include in ngen execution, empty if all from hydrofabric should be used.
    nexuses : Tuple[str]
        Collection of nexuses string ids to include in ngen execution, empty if all from hydrofabric should be used.

    Raises
    ------
    subprocess.CalledProcessError
        Raised if either the trial run for ngen or the valgrind memcheck call subprocess does not return 0.
    """
    cat_str = "all" if len(catchments) == 0 else ','.join(sorted(set(catchments)))
    nexus_str = "all" if len(nexuses) == 0 else ','.join(sorted(set(nexuses)))

    full_ngen_cmd = f"{NGEN_PATH} {catchment_file!s} {cat_str} {nexus_file!s} {nexus_str} {realization_config!s}"

    if not realization_config.is_file():
        raise RuntimeError(f"Given realization config for memcheck run '{realization_config!s}' doesn't exist!")

    if not skip_command_check:
        logger.info("Executing the configured ngen command to make sure it can complete successfully:")
        logger.debug(f"Command is:\n    {full_ngen_cmd}")
        trial_proc = subprocess.run(full_ngen_cmd.split(" "), cwd="/dmod/datasets/output")
        trial_proc.check_returncode()

    logger.info(f"Successful test execution of ngen with '{realization_config!s}'")
    logger.info(f"Now running valgrind memcheck with this config")

    # TODO: (later) with ability to use '--log-file=filename' it looks like there might be better support for running the MPI version of ngen also

    # TODO: (later) option to turn on '--gen-suppressions=yes' for valgrind to get suppression syntax if needed
    # TODO: (later) ^ and then use '--suppressions=<filename>' to apply those

    # See https://valgrind.org/docs/manual/manual-core.html#manual-core.basicopts for other --log-file format specifiers
    valgrind_out_log_pattern = f"/dmod/datasets/output/log_{realization_config.name.replace('.', '_')}.%n.txt"
    valgrind_opts = f"--read-inline-info=yes --leak-check=yes --read-var-info=yes --log-file={valgrind_out_log_pattern}"

    valgrind_cmd = f"valgrind {valgrind_opts} {full_ngen_cmd}"

    valgrind_proc = subprocess.run(valgrind_cmd.split(" "), cwd="/dmod/datasets/output")

    valgrind_proc.check_returncode()


def run_simple_for_config(realization_config_basename: str, skip_command_check: bool = False):
    """
    Run valgrind memcheck in one of the simple, bundeled setups with default hydrofabric and BMI configs.

    Use provided realization config, and assumed default/basic setup for hydrofabric and selected catchments.

    Parameters
    ----------
    realization_config_basename : Union[str, Path]
        Basename for the realization config, within ::attr:`EX_CFGS_DIR`.
    skip_command_check : bool
        If ``True`` (``False`` is the default), skip a check that ngen will actually run successfully with this config.

    Raises
    ------
    subprocess.CalledProcessError
        Raised if either the trial run for ngen or the valigrind memcheck call subprocess does not return 0.
    """

    run_valgrind(realization_config=EX_CFGS_DIR.joinpath(realization_config_basename),
                 catchment_file=Path(EXAMPLE_CATCHMENT_FILE),
                 nexus_file=Path(EXAMPLE_NEXUS_FILE),
                 skip_command_check=skip_command_check)


def _parse_args() -> argparse.Namespace:
    """
    Set up and run top-level arg parsing for module.

    Returns
    -------
    argparse.Namespace
        The parsed arguments namespace object.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog='run_memcheck',
                                     description="Run valgrind memcheck in this container on ngen exec and config.")
    parser.add_argument("--user-id", "-uid", dest="user_id", default=1000, help="Specify host user id for owning created files.")
    parser.add_argument("--group-id", "-gid", dest="group_id", default=1000, help="Specify host user id for owning created files.")
    # TODO: option to list example
    # TODO: option to pick example

    return parser.parse_args()


def _run_default_set_of_configs():
    #configs = ["memcheck_ex_02.json"]
    configs = ["memcheck_ex_01.json", "memcheck_ex_02.json"]

    for cfg in configs:
        try:
            run_simple_for_config(realization_config_basename=cfg)
            logger.info(f"Completed memcheck for {cfg}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Encountered error with config {cfg}")
            # TODO: (later) introduce option to skip and log message rather than fail and exit
            raise e


def main():
    """ Main routine for this script. """

    args = _parse_args()

    # Expect output base dir to exist, though it should not be created by image (i.e., because it gets bind-mounted into container)
    if not OUTPUT_BASE_DIR.is_dir():
        raise RuntimeError(f"Expected output base directory '{OUTPUT_BASE_DIR!s}' not mounted into container!")

    # TODO: option to pick example
    _run_default_set_of_configs()

    logger.info(f"Completed memcheck for desired configs.")

    # Finally, assign permissions
    logger.info(f"Setting correct ownership ({args.user_id!s}:{args.group_id!s}) for files in {OUTPUT_BASE_DIR!s}.")
    chown_proc = subprocess.run(["chown", "-R", f"{args.user_id!s}:{args.group_id!s}", f"{OUTPUT_BASE_DIR!s}"])
    chown_proc.check_returncode()


if __name__ == '__main__':
    main()
