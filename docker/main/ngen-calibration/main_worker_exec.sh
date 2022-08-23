#!/bin/sh

# Kick off exec of a multi-catchment, parallelized ngen-cal run, started from "main" worker that uses mpi_run
exec_main_worker()
{
    # Write (split) hoststring to a proper file
    mpi_host_file_init

    # Make sure all hosts are reachable, this also covers localhost
    mpi_host_check

    # Execute the parallelized ngen-cal run
    echo "$(print_date) Executing parallelized ngen-cal calibration on ${MPI_NODE_COUNT:?} workers"
    python ${CALIB_PY_MODULE:?} ${CALIB_CONFIG:?}

    # Capture the return value to use as service exit code
    CALIB_RETURN=$?

    echo "$(print_date) ngen-cal calibration command finished with return value: ${NGEN_RETURN}"

    # Close the other workers by removing this file
    signal_mpi_workers_shutdown

    # Exit with the model's exit code
    return ${CALIB_RETURN}

}