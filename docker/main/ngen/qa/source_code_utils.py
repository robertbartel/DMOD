import logging
import tarfile

from pathlib import Path


def link_or_extract_source(item: Path, dest_dir: Path, logger: logging.Logger):
    """
    Properly link or extract source code item into the provided destination directory.

    Place given source codes directory - which may be archived - into the given destination as a subdirectory. For any
    item that is itself a directory, create a symlink within the destination. For any item that is a tar file, extract
    the contents within the destination.  For other types of items, raise an error.

    Tar files are extracted fully to destination directory.  Note that it may often be assumed that the result of
    extracting the archive is the placement of a single new subdirectory, organized as a top-level container for
    some source code (i.e., tar file include a single, top-level directory, like a Git repo root).  No checks or
    manipulation to ensure that is done by this implementation.

    Parameters
    ----------
    item: Path
        A path to a source code subdirectory or subdirectory-containing archive/tarfile.
    dest_dir: Path
        Parent destination directory in which to link or extract the item directory.
    logger: logging.Logger
        A logging object.
    """
    # Symlink any source subdirectories
    if item.is_dir():
        logger.debug(f"Item {item!s} is a directory: creating symbolic link")
        symlink = dest_dir.joinpath(item.name)
        if symlink.exists():
            raise RuntimeError(f"Cannot symlink '{item!s}': somehow '{symlink!s}' already exists!")
        symlink.symlink_to(item)
    # Extract any tar files
    elif tarfile.is_tarfile(item):
        logger.debug(f"Item {item!s} is a tar file: extracting")
        tarfile.open(item).extractall(path=dest_dir)
    # Otherwise, error
    else:
        raise RuntimeError(f"Invalid item '{item.name}'; cannot prepare source except for directory or archive")