################################################################################################################
################################################################################################################
################################################################################################################
##### External Global Args Declaration and Defaults
################################################################################################################
# Any args that will need to be set, first declare them here, then later redeclare them within any stages.
# Also, for those with defaults, set those up here so that's easier to find.
ARG DOCKER_INTERNAL_REGISTRY

#FROM rockylinux:8.5 as rocky-base
FROM ${DOCKER_INTERNAL_REGISTRY}/ngen:latest

# TODO: install dmod.calibration, ngen-cal, and dependencies into python environment

# TODO: make sure expected calibration Python script/module path is set in CALIB_PY_SCRIPT
CALIB_PY_SCRIPT=

# Copy customized/altered main exec script
COPY --chown=${USER} main_worker_exec.sh ${WORKDIR}
