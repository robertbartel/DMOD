#!/bin/sh
# Managed by the _generate_docker_cmd_args function in scheduler.py of dmod.scheduler
#
# $1 will have the number of nodes associated with this run
# $2 will have comma-delimited host strings in MPI form; e.g., hostname:N,hostname:M
# $3 will have the unique job id
# $4 is the worker index
# $5 will be the name of the output dataset (which will imply a directory location)
# $6 will be the name of the hydrofabric dataset (which will imply a directory location)
# $7 will be the name of the realization configuration dataset (which will imply a directory location)
# $8 will be the name of the BMI configuration dataset (which will imply a directory location)
# $9 will be the name of the partition configuration dataset (which will imply a directory location)

MPI_NODE_COUNT="${1:?No MPI node count given}"
MPI_HOST_STRING="${2:?No MPI host string given}"
JOB_ID=${3:?No Job id given}
WORKER_INDEX=${4:?No worker index given}
OUTPUT_DATASET_NAME="${5:?}"
HYDROFABRIC_DATASET_NAME="${6:?}"
REALIZATION_CONFIG_DATASET_NAME="${7:?}"
BMI_CONFIG_DATASET_NAME="${8:?}"
PARTITION_DATASET_NAME="${9:?}"

# Source several common settings/variables and shared functions
source common.sh

set_mpi_host_file_path

# Sanity check that the output, hydrofabric, and config datasets are available (i.e., their directories are in place)
check_for_default_dataset_dirs

# Move to the output dataset mounted directory
cd ${OUTPUT_DATASET_DIR}

if [ "${WORKER_INDEX}" = "0" ]; then
    if [ "$(whoami)" = "${MPI_USER}" ]; then
        exec_main_worker_ngen_run
    else
        echo "$(print_date) Starting SSH daemon on main worker"
        /usr/sbin/sshd -D &
        _SSH_D_PID="$!"

        # Start the SSH daemon as a power user, but then actually run the model as our MPI_USER
        echo "$(print_date) Running exec script as '${MPI_USER:?}'"
        # Do this by just re-running this script with the same args, but as the other user
        # The script will modify its behavior as needed depending on current user (see associated "if" for this "else")
        _EXEC_STRING="${0} ${@}"
        su ${MPI_USER:?} --session-command "${_EXEC_STRING}"
        #time su ${MPI_USER:?} --session-command "${_EXEC_STRING}"

        # Once running the model finishes, kill the SSH daemon process
        kill ${_SSH_D_PID}
    fi
else
    echo "$(print_date) Starting SSH daemon, waiting for main job"
    /usr/sbin/sshd -D &
    _SSH_D_PID="$!"

    touch ${RUN_SENTINEL}
    chown ${MPI_USER} ${RUN_SENTINEL}
    while [ -e ${RUN_SENTINEL} ]; do
        sleep 5
    done

    kill ${_SSH_D_PID}
fi