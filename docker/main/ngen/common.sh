#!/bin/sh
###############################################################################
##### Variables
###############################################################################

# Define a few common/standard variables, which can be overridden with the
# right environment variable

if [ -z "${ACCESS_KEY_SECRET:-}" ]; then
    ACCESS_KEY_SECRET="object_store_exec_user_name"
fi
if [ -z "${SECRET_KEY_SECRET:-}" ]; then
    SECRET_KEY_SECRET="object_store_exec_user_passwd"
fi
if [ -z "${NGEN_EXECUTABLE:-}" ]; then
    #NGEN_EXECUTABLE="ngen"
    NGEN_EXECUTABLE="/ngen/ngen/cmake_build/ngen"
fi
if [ -z "${PYTHON_EXECUTABLE:-}" ]; then
    PYTHON_EXECUTABLE="python"
fi
if [ -z "${MPI_USER:-}" ]; then
    MPI_USER="mpi"
fi
if [ -z "${MPI_RUN:-}" ]; then
    MPI_RUN="mpirun"
fi
if [ -z "${RUN_SENTINEL:-}" ]; then
    RUN_SENTINEL="/home/${MPI_USER}/.run_sentinel"
fi

# Define several that are fixed (though perhaps relative to other things that have been set prior to them)
DOCKER_SECRETS_DIR="/run/secrets"
ACCESS_KEY_FILE="${DOCKER_SECRETS_DIR}/${ACCESS_KEY_SECRET}"
SECRET_KEY_FILE="${DOCKER_SECRETS_DIR}/${SECRET_KEY_SECRET}"
#
ALL_DATASET_DIR="/dmod/datasets"
OUTPUT_DATASET_DIR="${ALL_DATASET_DIR}/output/${OUTPUT_DATASET_NAME:?}"
HYDROFABRIC_DATASET_DIR="${ALL_DATASET_DIR}/hydrofabric/${HYDROFABRIC_DATASET_NAME:?}"
REALIZATION_CONFIG_DATASET_DIR="${ALL_DATASET_DIR}/config/${REALIZATION_CONFIG_DATASET_NAME:?}"
BMI_CONFIG_DATASET_DIR="${ALL_DATASET_DIR}/config/${BMI_CONFIG_DATASET_NAME:?}"
PARTITION_DATASET_DIR="${ALL_DATASET_DIR}/config/${PARTITION_DATASET_NAME:?}"

###############################################################################
##### Functions
###############################################################################

print_date()
{
    date "+%Y-%m-%d,%H:%M:%S"
}

set_mpi_host_file_path()
{
    if [ "$(whoami)" = "${MPI_USER:?}" ]; then
        MPI_HOSTS_FILE="${HOME}/.mpi_hosts"
    else
        MPI_HOSTS_FILE="$(su ${MPI_USER} -c 'echo "${HOME}"')/.mpi_hosts"
    fi
}

check_file_exists_or_bail()
{
    # File path is $1
    # File description is $2 (e.g. realization config)
    if [ ! -f "${1:?No file given to check for existence!}" ]; then
        >&2 echo "Error: ${2:-} file ${1} expected but does not exist"
        exit 1
    fi
}

check_for_dataset_dir()
{
    # Dataset dir is $1
    _CATEG="$(echo "${1}" | sed "s|${ALL_DATASET_DIR}/\([^/]*\)/.*|\1|" | awk '{print toupper($0)}')"
    if [ ! -d "${1}" ]; then
        echo "Error: expected ${_CATEG} dataset directory ${1} not found." 2>&1
        exit 1
    fi
}

# Sanity check that the "standard" output, hydrofabric, and config datasets are available (i.e., their directories are in place)
check_for_default_dataset_dirs()
{
    check_for_dataset_dir "${REALIZATION_CONFIG_DATASET_DIR:?}"
    check_for_dataset_dir "${BMI_CONFIG_DATASET_DIR:?}"
    check_for_dataset_dir "${PARTITION_DATASET_DIR:?}"
    check_for_dataset_dir "${HYDROFABRIC_DATASET_DIR:?}"
    check_for_dataset_dir "${OUTPUT_DATASET_DIR:?}"
}

load_object_store_keys_from_docker_secrets()
{
    # Read Docker Secrets files for Object Store access, if they exist
    if [ -z "${ACCESS_KEY_FILE:-}" ]; then
        echo "WARN: Cannot load object store access key when Docker secret file name not set"
    elif [ -e "${ACCESS_KEY_FILE}" ]; then
        ACCESS_KEY="$(cat "${ACCESS_KEY_FILE}")"
    else
        echo "WARN: Cannot load object store access key when Docker secret file does not exist"
    fi

    if [ -z "${SECRET_KEY_FILE:-}" ]; then
            echo "WARN: Cannot load object store secret key when Docker secret file name not set"
    elif [ -e "${SECRET_KEY_FILE}" ]; then
        SECRET_KEY="$(cat "${SECRET_KEY_FILE}")"
    else
        echo "WARN: Cannot load object store secret key when Docker secret file does not exist"
    fi

    test -n "${ACCESS_KEY:-}" && test -n "${SECRET_KEY:-}"
}

# Initialize MPI hosts file from provided hosts string
mpi_host_file_init()
{
    # Write (split) hoststring to a proper file
    if [ -e "${MPI_HOSTS_FILE:?Trying to initialize MPI host file without a path for it set}" ]; then
        rm "${MPI_HOSTS_FILE}"
    fi

    echo "$(print_date) Preparing MPI hosts file"
    for i in $(echo "${MPI_HOST_STRING:?Trying to create MPI hosts file without hosts string}" | sed 's/,/ /g'); do
        #echo "${i}" | awk -F: '{print $1 " slots=" $2}' >> "${MPI_HOSTS_FILE}"
        echo "${i}" | awk -F: '{print $1 ":" $2}' >> "${MPI_HOSTS_FILE}"
    done
}

# Check that the hosts from MPI hosts string are all online and ready for MPI scheduling
mpi_host_check()
{
    echo "$(print_date) Checking ${MPI_NODE_COUNT:-that} worker hosts are online for SSH"
    for i in $(echo "${MPI_HOST_STRING:?Trying to check if MPI hosts are online without host string}" | sed 's/,/ /g'); do
        _HOST_NAME=$(echo "${i}" | awk -F: '{print $1}')
        # Make sure all hosts are reachable, this also covers localhost
        until ssh -q ${_HOST_NAME} exit >/dev/null 2>&1; do :; done
        echo "DEBUG: Confirmed MPI host ${_HOST_NAME} is online for SSH"
    done
}

# Signal workers the can shut down by remotely deleting the sentinel file each watches for this
signal_mpi_workers_shutdown()
{
    for i in $(echo "${MPI_HOST_STRING}" | sed 's/,/ /g'); do
        _HOST_NAME=$(echo "${i}" | awk -F: '{print $1}')
        ssh -q ${_HOST_NAME} rm ${RUN_SENTINEL:?No run sentinel provided when try to shutdown MPI worker} >/dev/null 2>&1
    done

    echo "$(print_date) DEBUG: closed other worker SSH processes"
}
