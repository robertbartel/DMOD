import argparse
import subprocess
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from os import access as os_access
from os import X_OK as os_X_OK

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
EXAMPLE_HF_01_CATCHMENT_FILE = Path("/dmod/datasets/hydrofabric/ex_geojson_hf_01/catchment_data.geojson")
EXAMPLE_HF_01_NEXUS_FILE = Path("/dmod/datasets/hydrofabric/ex_geojson_hf_01/nexus_data.geojson")

EXAMPLE_HF_02_FILE = Path("/dmod/datasets/hydrofabric/ex_gpkg_hf_02_gauge_01073000/gauge_01073000.gpkg")

# TODO: make sure path to executable is set properly if we mess with paths
NGEN_PATH="/ngen/ngen/cmake_build/ngen"

OUTPUT_BASE_DIR = Path("/dmod/datasets/output")


@dataclass
class ConfigBundle:
    """ Bundle of the primary essential config files for running ngen: the realization config and hydrofabric files. """
    realization_config: Path
    catchment_file: Path
    nexus_file: Path


EXAMPLE_CONFIGS: List[ConfigBundle] = [
    ConfigBundle(realization_config=EX_CFGS_DIR.joinpath("memcheck_ex_01.json"),
                 catchment_file=EXAMPLE_HF_01_CATCHMENT_FILE,
                 nexus_file=EXAMPLE_HF_01_NEXUS_FILE),
    ConfigBundle(realization_config=EX_CFGS_DIR.joinpath("memcheck_ex_02.json"),
                 catchment_file=EXAMPLE_HF_01_CATCHMENT_FILE,
                 nexus_file=EXAMPLE_HF_01_NEXUS_FILE),
    ConfigBundle(realization_config=EX_CFGS_DIR.joinpath("memcheck_ex_03.json"),
                 catchment_file=EXAMPLE_HF_02_FILE,
                 nexus_file=EXAMPLE_HF_02_FILE),
    ConfigBundle(realization_config=EX_CFGS_DIR.joinpath("memcheck_ex_04.json"),
                 catchment_file=EXAMPLE_HF_02_FILE,
                 nexus_file=EXAMPLE_HF_02_FILE)
]


class NgenRunner:
    """ Simple class to facilitate running ngen. """

    def __init__(self, ngen_path: Path, config_bundle: ConfigBundle, working_dir: Path, logger_instance: logging.Logger,
                 catchments: Tuple[str] = tuple(), nexuses: Tuple[str] = tuple(), **kwargs):
        """
        Initialize and run some sanity checks.

        Parameters
        ----------
        ngen_path: Path
            The path to the ngen executable to use.
        config_bundle: ConfigBundle
            The primary config bundle to use to run ngen, containing paths for the realization config and hydrofabric.
        working_dir: Path
            The working directory from which to run the ngen process.
        logger_instance : logging.Logger
            A logging instance to use.
        catchments : Tuple[str]
            Collection of catchment string ids to include in the ngen run, empty if all from hydrofabric should be used.
        nexuses : Tuple[str]
            Collection of nexuses string ids to include in the ngen, empty if all from hydrofabric should be used.
        kwargs
            Other unused keyword args.
        """
        self._ngen_path = ngen_path
        self._config_bundle = config_bundle
        self._working_dir = working_dir
        self._catchments = catchments
        self._nexues = nexuses
        self._logger = logger_instance
        self._cmd_str = None

        if not self._ngen_path.is_file():
            raise ValueError(f"{self.__class__.__name__} given non-existing path '{ngen_path!s}' for ngen!")
        if not os_access(self._ngen_path, os_X_OK):
            raise ValueError(f"{self.__class__.__name__} given non-executable file '{ngen_path!s}' for ngen!")
        if not self.realization_config.is_file():
            raise ValueError(f"{self.__class__.__name__} given realization config '{self.realization_config!s}' that doesn't exist!")
        if not self._working_dir.is_dir():
            raise RuntimeError(f"{self.__class__.__name__} has working dir '{self._working_dir!s}' set that doesn't exist!")

    @property
    def catchment_file(self) -> Path:
        """ The path to the hydrofabric catchment file to use to run ngen. """
        return self._config_bundle.catchment_file

    @property
    def ngen_cmd_str(self) -> str:
        """ The appropriate string for the command to use to run ngen. """
        if self._cmd_str is None:
            cat_str = "all" if len(self._catchments) == 0 else ','.join(sorted(set(self._catchments)))
            nexus_str = "all" if len(self._nexues) == 0 else ','.join(sorted(set(self._nexues)))
            self._cmd_str = f"{self._ngen_path!s} {self._config_bundle.catchment_file!s} {cat_str} {self._config_bundle.nexus_file!s} {nexus_str} {self._config_bundle.realization_config!s}"
        return self._cmd_str

    @property
    def realization_config(self) -> Path:
        """ The path to the realization config to use to run ngen. """
        return self._config_bundle.realization_config

    def run(self):
        """ Run the ngen command from ::method:`cmd_str` using a subprocess. """
        self._logger.info("Executing the configured ngen command to make sure it can complete successfully:")
        self._logger.debug(f"Command is:\n    {self.ngen_cmd_str}")
        trial_proc = subprocess.run(self.ngen_cmd_str.split(" "), cwd=str(self._working_dir))
        try:
            trial_proc.check_returncode()
            self._logger.info(f"Successful test execution of ngen with '{self.realization_config!s}'")
        except Exception as e:
            logger.error(f"Check of command failed to execute successfully:\n {self.ngen_cmd_str}")
            raise e


class NgenMemcheckRunner(NgenRunner):
    """ Extension of ::class:`NgenRunner` specifically for running ngen through Valgrind Memcheck. """

    def __init__(self, output_dir: Path, skip_cmd_check: bool = False, **kwargs):
        """
        Initialize and run some sanity checks.

        Parameters
        ----------
        output_dir: Path
            Directory in which to write Memcheck output files.
        skip_cmd_check: bool
            Whether to skip running ngen without memcheck to validate the configuration.
        kwargs
            Additional keyword args as used by the superclass (see ``Other Parameters`` below).

        Other Parameters
        ----------------
        config_bundle: ConfigBundle
            The primary config bundle to use to run ngen, containing paths for the realization config and hydrofabric.
        working_dir: Path
            The working directory from which to run the ngen process.
        logger_instance : logging.Logger
            A logging instance to use.
        catchments : Tuple[str]
            Collection of catchment string ids to include in the ngen run, empty if all from hydrofabric should be used.
        nexuses : Tuple[str]
            Collection of nexuses string ids to include in the ngen, empty if all from hydrofabric should be used.
        """
        super().__init__(**kwargs)
        self._output_dir = output_dir
        self._skip_cmd_check = skip_cmd_check

        if not self._output_dir.is_dir():
            raise ValueError(f"{self.__class__.__name__} provided non-existing output dir '{output_dir!s}'!")

    def run(self):
        """ Run the ngen command from ::method:`cmd_str` optionally by itself and then through Valgrind Memcheck. """
        if not self._skip_cmd_check:
            super().run()
            self._logger.info(f"Now running valgrind memcheck with this config")
        else:
            self._logger.info("Executing the configured ngen command through valgrind memcheck.")
            self._logger.debug(f"Command is:\n    {self.ngen_cmd_str}")

        # TODO: (later) with ability to use '--log-file=filename' it looks like there might be better support for running the MPI version of ngen also

        # TODO: (later) option to turn on '--gen-suppressions=yes' for valgrind to get suppression syntax if needed
        # TODO: (later) ^ and then use '--suppressions=<filename>' to apply those

        # See https://valgrind.org/docs/manual/manual-core.html#manual-core.basicopts for other --log-file format specifiers
        valgrind_out_log_pattern = f"{self._output_dir!s}/log_{self.realization_config.name.replace('.', '_')}.%n.txt"
        valgrind_opts = f"--read-inline-info=yes --leak-check=yes --read-var-info=yes --log-file={valgrind_out_log_pattern}"

        valgrind_cmd = f"valgrind {valgrind_opts} {self.ngen_cmd_str}"

        valgrind_proc = subprocess.run(valgrind_cmd.split(" "), cwd=str(self._working_dir))

        valgrind_proc.check_returncode()


def _parse_args() -> argparse.Namespace:
    """
    Set up and run top-level arg parsing for module.

    Returns
    -------
    argparse.Namespace
        The parsed arguments namespace object.
    """

    def process_cfg_ex(realization_config_basename: str) -> ConfigBundle:
        ex_cfg_map = {c.realization_config.name: c for c in EXAMPLE_CONFIGS}
        if realization_config_basename in ex_cfg_map:
            return ex_cfg_map[realization_config_basename]
        else:
            raise ValueError(f"No example config file with basename '{realization_config_basename}'")

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog='run_memcheck',
                                     description="Run valgrind memcheck in this container on ngen exec and config.")

    parser.add_argument("--skip-cmd-check", dest="skip_cmd_check", action="store_true",
                        help="Set to not run ngen command(s) on its own first to validate.")

    parser.add_argument("--skip-memcheck", dest="skip_memcheck", action="store_true",
                        help="Set to not run memcheck and only run the config(s) through ngen to validate them.")

    parser.add_argument("--include-config", dest="included_configs", action="append", type=process_cfg_ex,
                        help="Include the given example config for processing (default is to process all of them).  "
                             "Configs are specified by the basename of the realization config file.  Choices are: {"
                             f"{' '.join([c.realization_config.name for c in EXAMPLE_CONFIGS])}" "}")

    parser.add_argument("--user-id", "-uid", dest="user_id", default=1000,
                        help="Specify host user id for owning created files.")

    parser.add_argument("--group-id", "-gid", dest="group_id", default=1000,
                        help="Specify host user id for owning created files.")

    # TODO: option to list example

    return parser.parse_args()


def main():
    """ Main routine for this script. """

    args = _parse_args()

    # Expect output base dir to exist, though it should not be created by image (i.e., because it gets bind-mounted into container)
    if not OUTPUT_BASE_DIR.is_dir():
        raise RuntimeError(f"Expected output base directory '{OUTPUT_BASE_DIR!s}' not mounted into container!")

    configs = args.included_configs if args.included_configs and len(args.included_configs) > 0 else EXAMPLE_CONFIGS

    RunnerClass = NgenRunner if args.skip_memcheck else NgenMemcheckRunner

    for cfg in configs:
        try:
            runner = RunnerClass(ngen_path=Path(NGEN_PATH), config_bundle=cfg, working_dir=OUTPUT_BASE_DIR,
                                 output_dir=OUTPUT_BASE_DIR, skip_cmd_check=args.skip_cmd_check, logger_instance=logger)
            runner.run()
            #run_valgrind(config_example=cfg, skip_command_check=args.skip_cmd_check)
            logger.info(f"Completed memcheck for {cfg.realization_config.name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Encountered error with config {cfg.realization_config.name}")
            # TODO: (later) introduce option to skip and log message rather than fail and exit
            raise e

    logger.info(f"Completed memcheck for desired configs.")

    # Finally, assign permissions
    logger.info(f"Setting correct ownership ({args.user_id!s}:{args.group_id!s}) for files in {OUTPUT_BASE_DIR!s}.")
    chown_proc = subprocess.run(["chown", "-R", f"{args.user_id!s}:{args.group_id!s}", f"{OUTPUT_BASE_DIR!s}"])
    chown_proc.check_returncode()


if __name__ == '__main__':
    main()
