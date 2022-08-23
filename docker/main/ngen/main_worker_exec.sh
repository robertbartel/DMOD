#!/bin/sh

# Kick off execution of a standard ngen framework run, assumed to be started from the "main" worker that uses mpi_run
exec_main_worker()
{
    # Write (split) hoststring to a proper file
    mpi_host_file_init

    # Make sure all hosts are reachable, this also covers localhost
    mpi_host_check

    # Execute the model on the linked data
    echo "$(print_date) Executing mpirun command for ngen on ${MPI_NODE_COUNT:?} workers"
    ${MPI_RUN:?} -f "${MPI_HOSTS_FILE:?}" -n ${MPI_NODE_COUNT} \
        ${NGEN_EXECUTABLE:?} ${HYDROFABRIC_DATASET_DIR:?}/catchment_data.geojson "" \
                ${HYDROFABRIC_DATASET_DIR:?}/nexus_data.geojson "" \
                ${REALIZATION_CONFIG_DATASET_DIR:?}/realization_config.json \
                ${PARTITION_DATASET_DIR:?}/partition_config.json \
                --subdivided-hydrofabric

    # Capture the return value to use as service exit code
    NGEN_RETURN=$?

    echo "$(print_date) ngen mpirun command finished with return value: ${NGEN_RETURN}"

    # Close the other workers by removing this file
    signal_mpi_workers_shutdown

    # Exit with the model's exit code
    return ${NGEN_RETURN}
}