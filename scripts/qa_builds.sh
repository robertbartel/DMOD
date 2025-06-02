#!/bin/bash

## Script to help with the building of ngen related images (e.g., ngen, ngen-qa) for QA and testing purposes

USAGE=$(cat <<HEREDOC
Script to help with the building of ngen related images (e.g., ngen, ngen-qa) for QA and testing purposes

Allows for building ngen related image without a full DMOD environment configuration, as otherwise some env variables have to be explicitly set for image building tools to work correctly.  Also supresses unnecessary init of Swarm networks.

Usage:
    ${0} [-h|--help]
    ${0} <image_service_name>...

E.g.:
    ${0} ngen
    ${0} ngen-build-test ngen

See related docker-build.yml for applicable image service names.
HEREDOC
)

if [ ${#} -lt 1 ]; then
    >&2 echo "Error: At least one argument must be provided to ${0}"
    exit 1
elif [ "${1}" == "-h" ]; then
    echo "${USAGE}"
    exit 0
elif [ "${1}" == "--help" ]; then
    echo "${USAGE}"
    exit 0
fi


if [ -e .env ]; then
    source .env
fi

##############################################################################################
##############################################################################################
### Make sure these env variables required by compose config are set to reasonable defaults
if [ -z "${DOCKER_INTERNAL_REGISTRY:-}" ]; then
    export DOCKER_INTERNAL_REGISTRY=127.0.0.1:5000
fi

if [ -z "${NGEN_REPO_URL:-}" ]; then
    export NGEN_REPO_URL=https://github.com/NOAA-OWP/ngen
fi

if [ -z "${NGEN_BRANCH:-}" ]; then
    export NGEN_BRANCH=master
fi
##############################################################################################

##############################################################################################
##############################################################################################
### Also, fill in several other "required" variables not required by the ngen-related images
export PYTHON_PACKAGE_DIST_NAME_SCHEDULER_SERVICE="blah"
export PYTHON_PACKAGE_DIST_NAME_SCHEDULER="blah"
export PYTHON_PACKAGE_DIST_NAME_COMMS="blah"
export PYTHON_PACKAGE_DIST_NAME_SUBSET_SERVICE="blah"
export PYTHON_PACKAGE_DIST_NAME_REQUEST_SERVICE="blah"
export PYTHON_PACKAGE_DIST_NAME_MODELDATA="blah"
export PYTHON_PACKAGE_DIST_NAME_ACCESS="blah"
export PYTHON_PACKAGE_DIST_NAME_EXTERNAL_REQUESTS="blah"
export PYTHON_PACKAGE_DIST_NAME_PARTITIONER_SERVICE="blah"
export PYTHON_PACKAGE_NAME_PARTITIONER_SERVICE="blah"
# Note these says NWM but are really for pre-ngen versions (i.e., 3.x) which we don't care about here
export NWM_REPO_URL="blah"
export NWM_BRANCH="blah"
##############################################################################################

# TODO: sanity check things better later

./scripts/control_stack.sh --no-init-networks --build-args "$*" main build
