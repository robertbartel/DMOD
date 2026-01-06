import subprocess
import logging

from datetime import datetime
from pathlib import Path
from typing import List

from source_code_utils import link_or_extract_source

# Hopefully this ends up being worth the trouble
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# TODO: (later) perhaps an option to control this
#logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

C_CPP_SOURCES_DIR = Path("/dmod/qa/c_cpp_sources")
SOURCES_DIR = Path("/dmod/qa/sources")
USER_SOURCES_DIR = Path("/dmod/qa/users_sources")
OUTPUT_DIR_PARENT: Path = Path("/dmod/datasets/output")


def exec_checks(directory: Path, output_dir: Path, cpp_std: str = "c++14", os_platform: str = "unix64",
                #enabled_checks: str = "performance,portability,missingInclude", use_xml: bool = True) -> bool:
                enabled_checks: str = "all", use_xml: bool = True) -> bool:
    """
    Execute CppCheck and run checks on the code in the given directory.

    The output file will be named analogously to the basename of ``directory``, in the format
    ``<basename>_cppcheck.<extension>``, where ``<<extension>>`` is either "txt" or "xml" depending on ``use_xml``.

    Parameters
    ----------
    directory: Path
        The directory on which to run cppcheck.
    output_dir: Path
        A directory in which to write the cppcheck output results file.
    cpp_std: str
        The CppCheck string for C++ standard when running checks (default: 'c++14').
    os_platform: str
        The CppCheck string for platform (indicating types and sizes) when running checks (default: 'unix64').
    enabled_checks: str
        Comma delimited string with additional enabled checks beyond CppCheck defaults
        (default: 'performance,portability,missingInclude').
    use_xml: bool
        Whether to use XML output for CppCheck.

    Returns
    -------
    bool
        Whether checks were successfully run for this directory.
    """
    # TODO: (later) might want to optionally parameterize this
    ignored_map = {
        'ngen': ['extern', 'test/googletest']
    }

    if not output_dir.is_dir():
        raise RuntimeError(f"Output directory '{output_dir!s}' does not exist or is not a directory")
    extension = "xml" if use_xml else "txt"
    output_file = output_dir.joinpath(f"{directory.name}_cppcheck.{extension}")

    if not directory.is_dir():
        logger.error(f"Not running CppCheck on provided non-directory '{directory!s}'")
        return False
    elif len([directory.iterdir()]) == 0:
        logger.error(f"Not running CppCheck on provided empty directory '{directory!s}'")
        return False

    flags = [f"--enable={enabled_checks.strip()}", "--force", f"--platform={os_platform}", f"--std={cpp_std}"]
    if use_xml:
        flags.append("--xml")
    # Handle flags for ignores
    if directory.name in ignored_map:
        for ignored_subdir in ignored_map[directory.name]:
            flags.extend(["-i", str(directory.joinpath(ignored_subdir))])
    # Handle flag for output file
    flags.append(f"--output-file={output_file!s}")

    command = ["cppcheck"] + flags + [f"{directory!s}"]
    logger.debug(f"CppCheck command to be run is: {' '.join(command)}")
    cppcheck_proc = subprocess.run(command)
    try:
        cppcheck_proc.check_returncode()
        logger.info(f"CppCheck run for '{directory.name}' with results in '{output_file!s}'")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Encountered {e.__class__.__name__} running CppCheck for '{directory!s}':")
        logger.error(str(e))
        return False


def main():
    if not SOURCES_DIR.is_dir():
        SOURCES_DIR.mkdir(exist_ok=True)

    if USER_SOURCES_DIR.is_dir():
        logger.info(f"Linking or extracting user-provided sources within '{USER_SOURCES_DIR!s}' to '{SOURCES_DIR!s}'")
        logger.info(f"(Skipping contents of '{C_CPP_SOURCES_DIR!s}')")
        for item in USER_SOURCES_DIR.iterdir():
            link_or_extract_source(item=item, dest_dir=SOURCES_DIR, logger=logger)
    # By default, link sources under /dmod/qa/c_cpp_sources to analog under /dmod/qa/sources
    else:
        logger.info(f"Falling back to default sources dir, since user-provided sources dir doesn't exists at "
                    f"path '{USER_SOURCES_DIR!s}'")
        logger.info(f"Linking default C/C++ sources within '{C_CPP_SOURCES_DIR!s}' to '{SOURCES_DIR!s}'")
        for default_item in C_CPP_SOURCES_DIR.iterdir():
            link_or_extract_source(item=default_item, dest_dir=SOURCES_DIR, logger=logger)

    # Preparing and create our output (sub)directory
    datetime_str_fmt = '%Y%m%d_%H%M%S'
    output_dir = OUTPUT_DIR_PARENT.joinpath(f"cppcheck_{datetime.now().strftime(datetime_str_fmt)}")
    output_dir.mkdir(parents=False, exist_ok=False)

    # At this point, there must be something in the sources directory
    problem_dirs: List[Path] = []
    for subdir in SOURCES_DIR.iterdir():
        if not exec_checks(directory=subdir, output_dir=output_dir):
            problem_dirs.append(subdir)
    if len(problem_dirs) == 0:
        logger.info("Checks run successfully")
    else:
        logger.error(f"Checks complete, but failed for the following: {','.join([p.name for p in problem_dirs])}")


if __name__ == '__main__':
    main()