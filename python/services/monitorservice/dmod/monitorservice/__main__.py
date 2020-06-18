import argparse
from . import name as package_name
from . import MonitorService
from dmod.monitor import QueMonitor
from os import getenv
from pathlib import Path


def _handle_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # TODO: need details for initiating the Docker client connection

    parser.add_argument('--port',
                        help='Set the appropriate listening port value',
                        dest='port',
                        type=int,
                        default=3014)
    parser.add_argument('--redis-host',
                        help='Set the host value for making Redis connections',
                        dest='redis_host',
                        default=None)
    parser.add_argument('--redis-pass',
                        help='Set the password value for making Redis connections',
                        dest='redis_pass',
                        default=None)
    parser.add_argument('--redis-port',
                        help='Set the port value for making Redis connections',
                        dest='redis_port',
                        default=None)

    parser.prog = package_name
    return parser.parse_args()


def _get_parsed_or_env_val(parsed_val, env_var_suffix, fallback):
    """
    Return either a passed parsed value, if it is not ``None``, the value from one of several environmental variables
    with a standard beginning to their name, if one is found with a non-``None`` value, or a given fallback value.

    When proceeding to check environment variables, the following variables are checked in the following order, with the
    first existing and non-``None`` value returned:

        - DOCKER_SECRET_REDIS_<SUFFIX>
        - REDIS_<SUFFIX>
        - DOCKER_REDIS_<SUFFIX>

    The actual names have ``<SUFFIX>`` replaced with the provided suffix parameter.

    Finally, the fallback value is returned when necessary.

    Parameters
    ----------
    parsed_val
    env_var_suffix
    fallback

    Returns
    -------
    The appropriate value, given the params and the existing environment variables.
    """
    if parsed_val is not None:
        return parsed_val
    env_prefixes = ['DOCKER_SECRET_REDIS_', 'REDIS_', 'DOCKER_REDIS_']
    for prefix in env_prefixes:
        env_var = prefix + env_var_suffix
        if getenv(env_var, None) is not None:
            return getenv(env_var)
    return fallback


def _redis_params(parsed_args) -> tuple:
    """
    Return the Redis host, port, and password for connections, obtained from the parsed arguments and/or environment.

    Parameters
    ----------
    parsed_args

    Returns
    -------
    tuple
        The Redis host, port, and password for connections.
    """
    host = _get_parsed_or_env_val(parsed_args.redis_host, 'HOST', 'localhost')
    port = _get_parsed_or_env_val(parsed_args.redis_port, 'PORT', 6379)
    passwd = _get_parsed_or_env_val(parsed_args.redis_pass, 'PASS', '')

    return host, port, passwd


def _sanity_check_path_arg(path_as_str, is_directory=False):
    path_value = Path(path_as_str)
    if not path_value.exists():
        return False
    if is_directory and not path_value.is_dir():
        return False
    if not is_directory and not path_value.is_file():
        return False
    return True


def main():
    args = _handle_args()

    # Sanity check any provided path arguments

    # Obtain Redis params
    redis_host, redis_port, redis_pass = _redis_params(args)

    monitor = QueMonitor('', redis_host=redis_host, redis_pass=redis_pass, redis_port=redis_port)

    # Init monitor service
    service = MonitorService(monitor=monitor)

    service.add_async_task(service.monitor_jobs())

    service.run()


if __name__ == '__main__':
    main()
