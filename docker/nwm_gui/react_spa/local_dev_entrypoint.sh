#!/bin/bash

# Sanity check the extras were set correctly
if [ ! -d "${HOST_MOUNT_SRC_DIR:?Env var for mounted host source not set for React local dev container}" ]; then
    >&2 echo "Expected host-mounted source directory '${HOST_MOUNT_SRC_DIR}' does not exist"
    exit 1
elif [ ! -d "${HOST_MOUNT_SRC_DIR}/src" ]; then
    >&2 echo "Invalid host-mounted source directory supplied: '${HOST_MOUNT_SRC_DIR}/src' does not exist"
fi

_NPM_PID=""

decho()
{
    if [ ${DEBUG_LEVEL:-0} -gt 0 ]; then
        echo "${@}"
    fi
}

npm_is_running()
{
    if [ -n "${_NPM_PID:-}" ]; then
        ps -p ${_NPM_PID} > /dev/null
        return $?
    else
        return 1
    fi
}

run_npm()
{
    if ! npm_is_running; then
        decho "Executing 'npm run' in background"
        #npm run >> /npm_log.out 2 >> /npm_log.err &
        npm start &
        _NPM_PID=$!
    else
        echo "WARN: attempting to start NPM when NPM proc ${_NPM_PID} is already running"
    fi
}

stop_prev_npm()
{
    if npm_is_running; then
        kill ${_NPM_PID}
        wait ${_NPM_PID}
    fi
}

perform_sync()
{
    echo "============================================================================================"
    date
    rsync -av --exclude=node_modules ${HOST_MOUNT_SRC_DIR:?}/ /${REACT_APP_NAME:?}
    echo "============================================================================================"
}

_SENTINEL=0

cleanup_before_exit()
{
    _SENTINEL=1
    stop_prev_npm
}

# Trap to make sure we "clean up" script activity before exiting
trap cleanup_before_exit 0 1 2 3 6 1

cd /${REACT_APP_NAME:?}

while [ ${_SENTINEL:-1} -eq 0 ]; do

    decho "Checking if source code is in sync"
    # Check for secondary sentinel file that will pause sync but keep things running
    if [ -e ${HOST_MOUNT_SRC_DIR:?}/.pause_sync ]; then
        decho "Bypassing sync check due to pause sentinel"
        sleep 5
    elif diff -ru --exclude="node_modules" ${HOST_MOUNT_SRC_DIR:?} /${REACT_APP_NAME:?} >/dev/null; then
        if npm_is_running; then
            decho "NPM is running; sleeping before next sync"
            sleep 5
        else
            decho "Sources in sync; starting NPM"
            run_npm
        fi
    else
        # If here, things are out of sync, so stop previous npm
        decho "Sources out of sync; stopping NPM and syncing"
        #stop_prev_npm
        perform_sync
    fi

done
