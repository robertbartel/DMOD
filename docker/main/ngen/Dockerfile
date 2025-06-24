################################################################################################################
################################################################################################################
################################################################################################################
##### External Global Args Declaration and Defaults
################################################################################################################
# Any args that will need to be set, first declare them here, then later redeclare them within stage that uses.
# Also, for those with defaults, set those up here so that's easier to find.
ARG DOCKER_INTERNAL_REGISTRY

# Swap or override this as needed (below are the "standard" types from
#   https://cmake.org/cmake/help/latest/manual/cmake-buildsystem.7.html#default-and-custom-configurations)
#ARG NGEN_BUILD_CONFIG_TYPE="Debug"
ARG NGEN_BUILD_CONFIG_TYPE="Release"
#ARG NGEN_BUILD_CONFIG_TYPE="RelWithDebInfo"
#ARG NGEN_BUILD_CONFIG_TYPE="MinSizeRel"

ARG DATASET_DIRECTORIES="config forcing hydrofabric observation output"

# A suffix to indicate something special about this build, and perhaps differentiate it slightly (e.g., for QA)
ARG IMAGE_BUILD_SUFFIX

# Passing the ARG variables from compose via .env file will squash these defaults with empty strings
# Seems like the work around is to replicate the default values in the build env, or to check for
# empty and set to default as is shown commented out below.
ARG REPO_URL=https://github.com/NOAA-OWP/ngen.git
ARG BRANCH=master
ARG COMMIT
# Helper flag to, if "true" AND if COMMIT is not set, `git pull --ff-only` within the repo dir just before building ngen
ARG REFRESH_BEFORE_BUILD=true
ARG WORKDIR=/ngen

ARG TROUTE_REPO_URL=https://github.com/NOAA-OWP/t-route.git
ARG TROUTE_BRANCH=master
ARG TROUTE_COMMIT

ARG NGEN_CAL_BRANCH=master
ARG NGEN_CAL_COMMIT

ARG LGAR_C_REPO_URL="https://github.com/NOAA-OWP/LGAR-C.git"
ARG LGAR_C_BRANCH="master"
ARG LGAR_C_COMMIT

ARG SAC_SMA_REPO_URL="https://github.com/NOAA-OWP/sac-sma.git"
ARG SAC_SMA_BRANCH="master"
ARG SAC_SMA_COMMIT

ARG SNOW_17_REPO_URL="https://github.com/NOAA-OWP/snow17.git"
ARG SNOW_17_BRANCH="master"
ARG SNOW_17_COMMIT

ARG SFT_REPO_URL="https://github.com/NOAA-OWP/SoilFreezeThaw.git"
ARG SFT_BRANCH="master"
ARG SFT_COMMIT

ARG SMP_REPO_URL="https://github.com/NOAA-OWP/SoilMoistureProfiles.git"
ARG SMP_BRANCH="main"
ARG SMP_COMMIT

#### Default arguments for required dependencies needed during various build stages
# The Rocky-Linux-based "base" stage, rocky-base
ARG ROCKY_BASE_REQUIRED="sudo openssh openssh-server bash git which"
# The Rocky-Linux-based "ngen-deps" stage, rocky-ngen-deps
# TODO: later look at separating build and run images again, and install static lib netcdf packages in run images
#ARG ROCKY_NGEN_DEPS_REQUIRED="mpich mpich-devel sudo gcc gcc-c++ make cmake tar git gcc-gfortran libgfortran \
#    python39 python39-devel python39-pip python39-numpy \
#    netcdf-cxx4-devel netcdf-cxx4-mpich-devel netcdf-fortran-devel netcdf-fortran-mpich-devel \
#    hdf5 hdf5-devel hdf5-mpich hdf5-mpich-devel \
#    bzip2 expat expat-devel flex bison udunits2 udunits2-devel"

ARG ROCKY_NGEN_DEPS_REQUIRED="sudo gcc gcc-c++ make cmake tar git gcc-gfortran libgfortran \
    python3 python3-devel python3-pip \
    bzip2 expat expat-devel flex bison udunits2 udunits2-devel zlib-devel sqlite-devel sqlite-libs gdal-devel"
# TODO: removed texinfo from list because it couldn't be found; make sure this doesn't lead to issues

ARG BOOST_VERSION=1.82.0
#mpich 3.2 doesn't work well gfortran 11 it seems, an alignment error crops up, but 3.3.2 seems to work...
ARG MPICH_VERSION="3.3.2"
ARG MIN_PYTHON="3.8.0"
ARG BLOSC2_VERSION

ARG NETCDF_C_VERSION=4.8.1
ARG NETCDF_CXX_VERSION=4.3.1
ARG NETCDF_FORTRAN_VERSION=4.6.0
ARG HD5_VERSION=1.10.9

# Work around Fortran MPI issue
ARG FCFLAGS="-w -fallow-argument-mismatch -O2"
ARG FFLAGS="-w -fallow-argument-mismatch -O2"

# Used to set analogous CMake env vars for adding default compilation flags
# But not for dependencies, like MPI, just ngen (and BMI modules)
ARG NGEN_CFLAGS
ARG NGEN_CXXFLAGS

ARG MPICH_CONFIGURE_OPTIONS="--enable-shared"
ARG MPICH_MAKE_OPTIONS

ARG BUILD_PARALLEL_JOBS

ARG NGEN_WITH_BMI_C="ON"
ARG NGEN_WITH_BMI_FORTRAN="ON"
ARG NGEN_WITH_PYTHON="ON"
ARG NGEN_WITH_NETCDF="ON"
# This one needs to be lowercase for some use in conditional build stages
ARG NGEN_WITH_ROUTING="on"
ARG NGEN_WITH_UDUNITS="ON"
ARG NGEN_UDUNITS_QUIET="ON"
ARG NGEN_WITH_SQLITE="ON"

ARG BUILD_NGEN_SERIAL="true"
ARG BUILD_NGEN_PARALLEL="true"
ARG BUILD_PARTITIONER="false"
ARG BUILD_NOAH_OWP="true"
ARG BUILD_CFE="true"
ARG BUILD_TOPMODEL="true"
ARG BUILD_PET="true"
ARG BUILD_SLOTH="true"

# BMI submodules (and fortran bindings) in ngen extern/ dir that should have shared libs copied to /dmod/shared_libs/
ARG NGEN_BMI_ACTIVE_SUBMODULES="iso_c_fortran_bmi noah-owp-modular topmodel cfe sloth evapotranspiration"

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for Rocky-Linux-based "base"
FROM rockylinux:9.1 as rocky-base

ARG USER=mpi
ENV USER=${USER} USER_HOME=/home/${USER}
ENV SSHDIR=${USER_HOME}/.ssh

ARG ROCKY_BASE_REQUIRED

RUN dnf update -y \
    && dnf install -y 'dnf-command(config-manager)' \
    && dnf config-manager --set-enabled crb \
    && dnf install -y epel-release \
    && dnf -y install ${ROCKY_BASE_REQUIRED} \
    && dnf -y clean all \
    # Note that adduser -p expects an encrypted/hashed password, so it will ignore a simple password \
    && adduser -p 'ignored' ${USER} \
    && echo "${USER}   ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && chown -R ${USER}:${USER} ${USER_HOME} \
    && cd /etc/ssh/ && ssh-keygen -A -N '' \
    # Config SSH Daemon \
    && sed -i "s/#PasswordAuthentication.*/PasswordAuthentication no/g" /etc/ssh/sshd_config \
    && sed -i "s/#PermitRootLogin.*/PermitRootLogin no/g" /etc/ssh/sshd_config \
    && sed -i "s/#AuthorizedKeysFile/AuthorizedKeysFile/g" /etc/ssh/sshd_config \
    # Unlock non-password USER to enable SSH login \
    #&& passwd -u ${USER} \
    # Set up user's public and private keys \
    && mkdir -p ${SSHDIR} \
    # Create DMOD-specific directory structure \
    && mkdir -p /dmod && chown ${USER} /dmod \
    && mkdir -p /dmod/local_volumes && chown ${USER} /dmod/local_volumes \
    && mkdir -p /dmod/cluster_volumes && chown ${USER} /dmod/cluster_volumes \
    && mkdir -p /dmod/datasets && chown ${USER} /dmod/datasets \
    #&& mkdir -p /dmod/shared_libs && chown ${USER} /dmod/shared_libs \
    && mkdir -p /dmod/lib && chown ${USER} /dmod/lib \
    && mkdir -p /dmod/lib64 && chown ${USER} /dmod/lib64 \
    && mkdir -p /dmod/include && chown ${USER} /dmod/include \
    && mkdir -p /dmod/bmi_module_data && chown ${USER} /dmod/bmi_module_data \
    && mkdir -p /dmod/bin && chown ${USER} /dmod/bin  \
    && mkdir -p /dmod/serial_bin && chown ${USER} /dmod/serial_bin  \
    # Default ssh config file that skips (yes/no) question when first login to the host \
    && echo "Host *" > ${SSHDIR}/config \
    && echo "    StrictHostKeyChecking no" >> ${SSHDIR}/config \
    && echo "    TCPKeepAlive yes" >> ${SSHDIR}/config \
    && echo "    ServerAliveCountMax 6" >> ${SSHDIR}/config \
    && echo "    ServerAliveInterval 30" >> ${SSHDIR}/config

USER root

COPY ssh ${SSHDIR}/

ARG WORKDIR

RUN cat ${SSHDIR}/*.pub >> ${SSHDIR}/authorized_keys \
    && chmod -R 600 ${SSHDIR}/* \
    && chown -R ${USER}:${USER} ${SSHDIR} \
    && mkdir -p ${WORKDIR} \
    && chown -R ${USER}:${USER} ${WORKDIR} \
    && echo "cd ${WORKDIR}" >> ${USER_HOME}/.profile \
    && chown ${USER}:${USER} ${USER_HOME}/.profile \
    && cp -a ${USER_HOME}/.profile ${USER_HOME}/.bash_profile

# Switch back to default user when continue the build process
USER ${USER}

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading Boost
FROM rockylinux:9.1 AS download_boost

# Redeclaring inside this stage to get default from before first FROM
ARG BOOST_VERSION

# Copy this file here is just to avoid failure if there is no boost_*.tar.* present.
# Use essentially a dummy file that won't change (unless someone does that deliberately to trigger a full rebuild), as
#   any change to this file will cause anything and and build layer/stage that uses boost to be fully rebuilt.
COPY .boost_local_copying.md boost_*.tar.* ${WORKDIR}

RUN mkdir /boost \
    && if compgen -G "${WORKDIR}/boost_${BOOST_VERSION//./_}.tar.*" > /dev/null; then \
        mv ${WORKDIR}/boost_${BOOST_VERSION//./_}.tar.* /boost/boost_tarball.blob ; \
    else \
        curl -L -o /boost/boost_tarball.blob https://sourceforge.net/projects/boost/files/boost/${BOOST_VERSION}/boost_${BOOST_VERSION//./_}.tar.bz2/download ; \
    fi

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading MPICH
FROM rockylinux:9.1 AS download_mpich

# Redeclaring inside this stage to get default from before first FROM
ARG MPICH_VERSION

RUN curl -o /tmp/mpich-${MPICH_VERSION}.tar.gz https://www.mpich.org/static/downloads/${MPICH_VERSION}/mpich-${MPICH_VERSION}.tar.gz


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading MPICH
FROM rockylinux:9.1 AS download_hd5

# Redeclaring inside this stage to get default from before first FROM
ARG HD5_VERSION

RUN curl -o /tmp/hdf5-${HD5_VERSION}.tar.gz https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-${HD5_VERSION}/src/hdf5-${HD5_VERSION}.tar.gz

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading netcdf
FROM rocky-base AS download_netcdf

# Redeclaring inside this stage to get default from before first FROM
ARG NETCDF_C_VERSION

RUN if [[ "${NETCDF_C_VERSION}" == "latest" ]]; then \
            curl -s https://api.github.com/repos/Unidata/netcdf-c/releases/latest \
                | grep "tarball_url" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-${NETCDF_C_VERSION}.tar.gz ; \
        else \
            curl -s https://api.github.com/repos/Unidata/netcdf-c/releases \
                | grep "tarball_url" \
                | grep "${NETCDF_C_VERSION}" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-${NETCDF_C_VERSION}.tar.gz ; \
        #fi \
        #&& mkdir /tmp/netcdf \
        #&& tar -xzf /tmp/netcdf-${NETCDF_C_VERSION}.tar.gz -C /tmp/netcdf --strip 1 \
        #&& rm /tmp/netcdf-${NETCDF_C_VERSION}.tar.gz
        fi

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading netcdf-fortran
FROM rocky-base AS download_netcdf_fortran

# Redeclaring inside this stage to get default from before first FROM
ARG NETCDF_FORTRAN_VERSION

RUN if [[ "${NETCDF_FORTRAN_VERSION}" == "latest" ]]; then \
            curl -s https://api.github.com/repos/Unidata/netcdf-fortran/releases/latest \
                | grep "tarball_url" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz ; \
        else \
            curl -s https://api.github.com/repos/Unidata/netcdf-fortran/releases \
                | grep "tarball_url" \
                | grep "${NETCDF_FORTRAN_VERSION}" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz ; \
        #fi \
        #&& mkdir /tmp/netcdf-fortran \
        #&& tar -xzf /tmp/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz -C /tmp/netcdf-fortran --strip 1 \
        #&& rm /tmp/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz
        fi

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for downloading NetCDF C++
FROM rocky-base AS download_netcdf_cxx

# Redeclaring inside this stage to get default from before first FROM
ARG NETCDF_CXX_VERSION

RUN if [[ "${NETCDF_CXX_VERSION}" == "latest" ]]; then \
            curl -s https://api.github.com/repos/Unidata/netcdf-cxx4/releases/latest \
                | grep "tarball_url" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz ; \
        else \
            curl -s https://api.github.com/repos/Unidata/netcdf-cxx4/releases \
                | grep "tarball_url" \
                | grep "${NETCDF_CXX_VERSION}" \
                | cut -d '"' -f 4 \
                | xargs curl -L -o /tmp/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz ; \
        #fi \
        #&& mkdir /tmp/netcdf-cxx4 \
        #&& tar -xzf /tmp/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz -C /tmp/netcdf-cxx4 --strip 1 \
        #&& rm /tmp/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz
        fi
    # This URL might also work for the analogous version:
    #   https://downloads.unidata.ucar.edu/netcdf-cxx/4.3.1/netcdf-cxx4-4.3.1.tar.gz
################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for just prior to "ngen-deps" for installing packaged deps
FROM rocky-base as rocky-ngen-packaged-deps

ARG ROCKY_NGEN_DEPS_REQUIRED

# Set up pip constraints file for this and descendent stages
COPY constraints.txt ${WORKDIR}/constraints.txt
ENV PIP_CONSTRAINT=${WORKDIR}/constraints.txt

# TODO: later, go back and change all pip3/python3 to just pip/python (but leave for now to limit scope)
# Note that this includes numpy, which is needed for Python BMI support, regardless of BMI module
USER root
RUN dnf update -y \
    &&  if [[ "${NGEN_BUILD_CONFIG_TYPE:-}" == "Debug" ]] || [[ "${NGEN_BUILD_CONFIG_TYPE:-}" == "RelWithDebInfo" ]]; then \
            dnf install -y ${ROCKY_NGEN_DEPS_REQUIRED} python3-debug; \
            ln -s $(which python3-debug) $(which python3 | sed 's/python3/python/'); \
        else \
            dnf install -y ${ROCKY_NGEN_DEPS_REQUIRED}; \
            ln -s $(which python3) $(which python3 | sed 's/python3/python/'); \
        fi \
    && dnf install -y ${ROCKY_NGEN_DEPS_REQUIRED} \
    && dnf clean -y all \
    #&& ln -s $(which python3) $(which python3 | sed 's/python3/python/') \
    && pip3 install --no-cache-dir pip wheel packaging \
    && if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then pip3 install --no-cache-dir numpy; fi
USER ${USER}

ENV FC=gfortran

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building t-route in Rocky Linux environment
FROM rocky-base as rocky_init_troute_repo
ARG TROUTE_REPO_URL
ARG TROUTE_BRANCH
ARG TROUTE_COMMIT
ARG WORKDIR

WORKDIR ${WORKDIR}

RUN cd ${WORKDIR} \
    && git clone --single-branch --branch $TROUTE_BRANCH $TROUTE_REPO_URL \
    && cd ./t-route \
    && if [ "x$TROUTE_COMMIT" != "x" ]; then git checkout $TROUTE_COMMIT; fi \
    && git submodule update --init

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for Rocky-Linux-based "ngen-deps"
FROM rocky-ngen-packaged-deps as rocky-ngen-deps

ARG BOOST_VERSION
ARG WORKDIR

ENV WORKDIR=${WORKDIR}
ENV BOOST_ROOT=${WORKDIR}/boost

COPY --chown=${USER} --from=download_boost /boost ${WORKDIR}/boost

ARG MPICH_VERSION
ARG MIN_PYTHON
ARG BLOSC2_VERSION
ARG ROCKY_NGEN_DEPS_REQUIRED

ARG MPICH_CONFIGURE_OPTIONS
ARG MPICH_MAKE_OPTIONS
ARG HD5_VERSION
ARG NETCDF_C_VERSION
ARG NETCDF_CXX_VERSION
ARG NETCDF_FORTRAN_VERSION

ENV MPICH_CONFIGURE_OPTIONS=${MPICH_CONFIGURE_OPTIONS}
ENV MPICH_MAKE_OPTIONS=${MPICH_MAKE_OPTIONS}
ENV HD5_VERSION=${HD5_VERSION}
ENV NETCDF_C_VERSION=${NETCDF_C_VERSION}
ENV NETCDF_CXX_VERSION=${NETCDF_CXX_VERSION}
ENV NETCDF_FORTRAN_VERSION=${NETCDF_FORTRAN_VERSION}

ARG NGEN_WITH_ROUTING

COPY --from=download_mpich /tmp/mpich-${MPICH_VERSION}.tar.gz /tmp/ngen-deps/mpich-${MPICH_VERSION}.tar.gz
COPY --from=download_hd5 /tmp/hdf5-${HD5_VERSION}.tar.gz /tmp/ngen-deps/hdf5-${HD5_VERSION}.tar.gz
COPY --from=download_netcdf /tmp/netcdf-${NETCDF_C_VERSION}.tar.gz /tmp/ngen-deps/netcdf-${NETCDF_C_VERSION}.tar.gz
COPY --from=download_netcdf_cxx /tmp/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz /tmp/ngen-deps/netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz
COPY --from=download_netcdf_fortran /tmp/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz /tmp/ngen-deps/netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz

USER root

ENV HYDRA_HOST_FILE=/etc/opt/hosts

# Hostfile location for mpirun. This file will be updated automatically.
RUN echo "export HYDRA_HOST_FILE=${HYDRA_HOST_FILE}" >> /etc/profile \
    && touch ${HYDRA_HOST_FILE} \
    && chown ${USER}:${USER} ${HYDRA_HOST_FILE} \
    ################### Build and install dependencies from source ################### \
    ##### Prep temp build root directory \
    && mkdir -p /tmp/ngen-deps \
    ##### Build and install mpich \
    && cd /tmp/ngen-deps \
    && tar xfz mpich-${MPICH_VERSION}.tar.gz  \
    && cd mpich-${MPICH_VERSION} \
    # mpich3 and gfortran > 10 don't get along...https://gcc.gnu.org/bugzilla/show_bug.cgi?id=91731 \
    && FFLAGS="-w -fallow-argument-mismatch -O2"  ./configure ${MPICH_CONFIGURE_OPTIONS} \
    && make -j ${BUILD_PARALLEL_JOBS} ${MPICH_MAKE_OPTIONS} && make install \
    ##### Build and install HDF5 \
    && cd /tmp/ngen-deps \
    && tar -xzf hdf5-${HD5_VERSION}.tar.gz \
    && cd hdf5-${HD5_VERSION} \
    && ./configure --enable-parallel --prefix=/usr \
    && make -j ${BUILD_PARALLEL_JOBS} && make install \
    ##### Build and install NetCDF C \
    && cd /tmp/ngen-deps \
    && mkdir netcdf \
    && tar -xzf netcdf-${NETCDF_C_VERSION}.tar.gz -C netcdf --strip 1 \
    && cd netcdf \
    # Make sure the netcdf prefix and install dirs align with t-route env var NETCDFINC set a little further below \
    && LIBS=curl && ./configure --enable-shared --prefix=/usr \
    && make -j ${BUILD_PARALLEL_JOBS} && make install \
    # TODO: if we run into any problem, might need to reactivate this \
    #&& make check \
    ##### Build and install NetCDF Fortran \
    && cd /tmp/ngen-deps \
    && mkdir netcdf-fortran \
    && tar -xzf netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz -C netcdf-fortran --strip 1 \
    && cd netcdf-fortran \
    && export NCDIR=/usr NFDIR=/usr \
    && LD_LIBRARY_PATH=/usr/lib CPPFLAGS=-I/usr/include LDFLAGS=-L/usr/lib ./configure --prefix=/usr \
    && make -j ${BUILD_PARALLEL_JOBS} && make install \
    ##### Build and install NetCDF C++ \
    && cd /tmp/ngen-deps \
    && mkdir netcdf-cxx4 \
    && tar -xzf netcdf-cxx4-${NETCDF_CXX_VERSION}.tar.gz -C netcdf-cxx4 --strip 1 \
    && mkdir netcdf-cxx4/build \
    && cd netcdf-cxx4/build \
    && cmake .. \
    && make -j ${BUILD_PARALLEL_JOBS} \
    # TODO: if we run into any problem, might need to reactivate this \
    # && ctest \
    && make install \
    # Set the regular user as the owner of the BOOST_ROOT dir we copied in \
    && chown -R ${USER}:${USER} ${BOOST_ROOT} \
    && rm -rf /tmp/ngen-deps

ENV PATH=${PATH}:/usr/lib64/mpich/bin
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib:/usr/local/lib64
# This next value is eventually needed for the t-route build ...
# ... make sure it stays in sync with configure step for netcdf above
ENV NETCDFINC=/usr/include
ENV CC=gcc

# Get this for the times we need to install t-route
COPY --from=rocky_init_troute_repo ${WORKDIR}/t-route/requirements.txt ${WORKDIR}/t-route-requirements.txt

USER ${USER}

# Set/pass provided C/C++ flags here for the rest of things
ARG NGEN_CXXFLAGS
ARG NGEN_CFLAGS
ENV CXXFLAGS=${NGEN_CXXFLAGS}
ENV CFLAGS=${NGEN_CFLAGS}

################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building framework in Rocky Linux environment
FROM rocky-base as rocky_init_repo
ARG REPO_URL
ARG NGEN_BUILD_CONFIG_TYPE
ARG BRANCH
ARG COMMIT
ARG WORKDIR

WORKDIR ${WORKDIR}

RUN cd ${WORKDIR} \
    && if [ "x$COMMIT" != "x" ]; then \
        git clone --single-branch --branch $BRANCH $REPO_URL \
        && cd ./ngen \
        && git checkout $COMMIT; \
    else \
        git clone --depth 1 --branch $BRANCH $REPO_URL \
        && cd ./ngen ; \
    fi \
    && echo "#!/bin/bash" > build_sub \
    && echo "cmake -B \$1/cmake_build -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE} -S \$1" >> build_sub \
    && echo "cmake --build \$1/cmake_build" >> build_sub \
    #&& echo "cd \$1/cmake_build && make install" >> build_sub \
    && chmod u+x build_sub \
    && git submodule update --init --depth 1 test/googletest \
    && git submodule update --init --recursive --depth 1

################################################################################################################
################################################################################################################
###### Create intermediate Docker build stage for building t-route in Rocky Linux environment
FROM rocky-ngen-deps as rocky_build_troute

ARG TROUTE_REPO_URL
ARG TROUTE_BRANCH
ARG TROUTE_COMMIT
ARG BUILD_PARALLEL_JOBS
ARG NGEN_WITH_ROUTING

COPY --chown=${USER} --from=rocky_init_troute_repo ${WORKDIR}/t-route ${WORKDIR}/t-route

#    && python(){ /usr/bin/python3 \$@; } && export -f python \
RUN if [ "${NGEN_WITH_ROUTING}" == "on" ]; then \
      export FC=gfortran ; \
      export F90=gfortran ; \
      mkdir ${WORKDIR}/t-route/wheels \
      && cd ${WORKDIR}/t-route \
      && pip install --no-cache-dir build wheel \
      && sed -i 's/build_[a-z]*=/#&/' compiler.sh \
      && ./compiler.sh no-e \
      && pip install --no-cache-dir -r requirements.txt \
      && pip install --config-setting='--build-option=--use-cython' src/troute-network/ \
      && python -m build --wheel --config-setting='--build-option=--use-cython' src/troute-network/ \
      && pip install --no-build-isolation --config-setting='--build-option=--use-cython' src/troute-routing/ \
      && python -m build --wheel --no-isolation --config-setting='--build-option=--use-cython' src/troute-routing/ \
      && pip install --no-cache-dir setuptools-scm \
      && python -m build --wheel --no-isolation src/troute-config/ \
      && python -m build --wheel --no-isolation src/troute-nwm/ \
      && cp src/troute-*/dist/*.whl wheels/. ; \
    fi

USER root
RUN rm /usr/bin/python
USER ${USER}


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building LGAR_C
FROM rocky-ngen-deps as build_bmi_lgar_c

ARG NGEN_BUILD_CONFIG_TYPE
ARG LGAR_C_REPO_URL
ARG LGAR_C_BRANCH
ARG LGAR_C_COMMIT

RUN git clone \
        --single-branch \
        --branch ${LGAR_C_BRANCH:?No lgar-c branch set} \
        ${LGAR_C_REPO_URL:?No lgar-c repo set} \
        ${WORKDIR}/lgar-c \
    && cd ${WORKDIR}/lgar-c \
    && if [ "x$LGAR_C_COMMIT" != "x" ]; then git checkout $LGAR_C_COMMIT ; fi \
    && cmake -B ./cmake_build \
            -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} \
            -DNGEN=ON  \
            -DCMAKE_INSTALL_PREFIX:PATH=/dmod \
            -S . \
    && cmake --build ./cmake_build \
    && cmake --build ./cmake_build --target install \
    && mkdir -p /dmod/shared_libs \
    && cp -a /dmod/lib64/liblasambmi.so* /dmod/shared_libs/ \
    # An extra bit here for copying lgar-c data \
    && mkdir -p /dmod/bmi_module_data/lgar-c/data \
    && cp -a ./data/ /dmod/bmi_module_data/lgar-c/data/ \
    # Clean-up a little more for Release builds \
    && if [ "${NGEN_BUILD_CONFIG_TYPE}" == "Release" ]; then cd ${WORKDIR} && rm -rf ${WORKDIR}/lgar-c ; fi


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building SoilFreezeThaw
FROM rocky-ngen-deps as build_bmi_sft

ARG NGEN_BUILD_CONFIG_TYPE
ARG SFT_REPO_URL
ARG SFT_BRANCH
ARG SFT_COMMIT

RUN git clone \
        --single-branch \
        --branch ${SFT_BRANCH:?No SoilFreezeThaw branch set} \
        ${SFT_REPO_URL:?No SoilFreezeThaw repo set} \
        ${WORKDIR}/SoilFreezeThaw \
    && cd ${WORKDIR}/SoilFreezeThaw \
    && if [ "x$SFT_COMMIT" != "x" ]; then git checkout $SFT_COMMIT ; fi \
    && cmake -B ./cmake_build \
            -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} \
            -DNGEN=ON  \
            -DCMAKE_INSTALL_PREFIX:PATH=/dmod \
            -S . \
    && cmake --build ./cmake_build \
    && cmake --build ./cmake_build --target install \
    && mkdir -p /dmod/shared_libs \
    && cp -a /dmod/lib64/libsftbmi.so* /dmod/shared_libs/ \
    # Clean-up a little more for Release builds \
    && if [ "${NGEN_BUILD_CONFIG_TYPE}" == "Release" ]; then cd ${WORKDIR} && rm -rf ${WORKDIR}/SoilFreezeThaw ; fi


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building SoilMoistureProfiles
FROM rocky-ngen-deps as build_bmi_smp

ARG NGEN_BUILD_CONFIG_TYPE
ARG SMP_REPO_URL
ARG SMP_BRANCH
ARG SMP_COMMIT

RUN git clone \
        --single-branch \
        --branch ${SMP_BRANCH:?No SoilMoistureProfiles branch set} \
        ${SMP_REPO_URL:?No SoilMoistureProfiles repo set} \
        ${WORKDIR}/SoilMoistureProfiles \
    && cd ${WORKDIR}/SoilMoistureProfiles \
    && if [ "x$SMP_COMMIT" != "x" ]; then git checkout $SMP_COMMIT ; fi \
    && cmake -B ./cmake_build \
            -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} \
            -DNGEN=ON  \
            -DCMAKE_INSTALL_PREFIX:PATH=/dmod \
            -S . \
    && cmake --build ./cmake_build \
    && cmake --build ./cmake_build --target install \
    && mkdir -p /dmod/shared_libs \
    && cp -a /dmod/lib64/libsmpbmi.so* /dmod/shared_libs/ \
    # Clean-up a little more for Release builds \
    && if [ "${NGEN_BUILD_CONFIG_TYPE}" == "Release" ]; then cd ${WORKDIR} && rm -rf ${WORKDIR}/SoilMoistureProfiles ; fi


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building ISO_C_BINDINGS for Fortran BMI modules
FROM rocky-ngen-deps as pre_build_bmi_iso_c_fortran_dep

ARG NGEN_BUILD_CONFIG_TYPE

COPY --chown=${USER} --from=rocky_init_repo ${WORKDIR}/ngen/extern/iso_c_fortran_bmi ${WORKDIR}/iso_c_fortran_bmi
WORKDIR ${WORKDIR}
RUN cmake -B ./iso_c_fortran_bmi/cmake_build -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} -S ./iso_c_fortran_bmi \
    && cmake --build ./iso_c_fortran_bmi/cmake_build


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building Sac-SMA
FROM rocky-ngen-deps as build_bmi_sac_sma

ARG NGEN_BUILD_CONFIG_TYPE
ARG SAC_SMA_REPO_URL
ARG SAC_SMA_BRANCH
ARG SAC_SMA_COMMIT

COPY --chown=${USER} --from=pre_build_bmi_iso_c_fortran_dep ${WORKDIR}/iso_c_fortran_bmi ${WORKDIR}/iso_c_fortran_bmi

# Note the second layer in the directory structure (i.e., sac-sma/sac-sma is the actual repo dir)
# Doing this to align with repo instructions
RUN mkdir ${WORKDIR}/sac-sma \
    && git clone \
        --single-branch \
        --branch ${SAC_SMA_BRANCH:?No sac-sma branch set} \
        ${SAC_SMA_REPO_URL:?No sac-sma repo set} \
        ${WORKDIR}/sac-sma/sac-sma \
    && cd ${WORKDIR}/sac-sma \
    && if [ "x$SAC_SMA_COMMIT" != "x" ]; then cd ./sac-sma && git checkout $SAC_SMA_COMMIT && cd .. ; fi \
    && cp ./sac-sma/ngen_files/sacbmi.pc.in ./sac-sma/ngen_files/CMakeLists.txt . \
    && cmake -B ./cmake_build -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} -DCMAKE_INSTALL_PREFIX:PATH=/dmod -S . \
    && cmake --build ./cmake_build --target all \
    && mkdir -p /dmod/shared_libs \
    && cp -a ./cmake_build/*.so* /dmod/lib64/. \
    && cp -a ./cmake_build/*.so* /dmod/shared_libs/. \
    # Clean-up a little more for Release builds \
    && if [ "${NGEN_BUILD_CONFIG_TYPE}" == "Release" ]; then cd ${WORKDIR} && rm -rf ${WORKDIR}/sac-sma ; fi


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building SNOW_17
FROM rocky-ngen-deps as build_bmi_snow_17

ARG NGEN_BUILD_CONFIG_TYPE
ARG SNOW_17_REPO_URL
ARG SNOW_17_BRANCH
ARG SNOW_17_COMMIT

# Snow17 needs iso_c_fortran_bmi built, and it needs it at ../iso_c_fortran_bmi (i.e., as if snow17 was under extern)

COPY --chown=${USER} --from=pre_build_bmi_iso_c_fortran_dep ${WORKDIR}/iso_c_fortran_bmi ${WORKDIR}/iso_c_fortran_bmi

RUN git clone \
        --single-branch \
        --branch ${SNOW_17_BRANCH:?No snow-17 branch set} \
        ${SNOW_17_REPO_URL:?No snow-17 repo set} \
        ${WORKDIR}/snow-17 \
    && cd ${WORKDIR}/snow-17 \
    && if [ "x$SNOW_17_COMMIT" != "x" ]; then git checkout $SNOW_17_COMMIT ; fi \
    && cmake -B ./cmake_build -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE:?} -DCMAKE_INSTALL_PREFIX:PATH=/dmod -S . \
    && cmake --build ./cmake_build \
    && mkdir -p /dmod/shared_libs \
    && cp -a ./cmake_build/*.so* /dmod/lib64/. \
    && cp -a ./cmake_build/*.so* /dmod/shared_libs/. \
    # Clean-up a little more for Release builds \
    && if [ "${NGEN_BUILD_CONFIG_TYPE}" == "Release" ]; then cd ${WORKDIR} && rm -rf ${WORKDIR}/snow-17 ; fi


################################################################################################################
################################################################################################################
##### Create 2 intermediate build stages for conditional control over whether routing stuff gets done
FROM rocky-ngen-deps AS pre_ngen_build_routing_OFF
COPY --chown=${USER} --from=rocky_init_repo ${WORKDIR}/ngen ${WORKDIR}/ngen
################################################################################################################
FROM rocky-ngen-deps AS pre_ngen_build_routing_ON
COPY --chown=${USER} --from=rocky_init_repo ${WORKDIR}/ngen ${WORKDIR}/ngen
COPY --chown=${USER} --from=rocky_build_troute ${WORKDIR}/t-route/wheels /tmp/t-route-wheels
COPY --chown=${USER} --from=rocky_build_troute ${WORKDIR}/t-route/src/kernel /tmp/t-route-kernels
COPY --chown=${USER} --from=rocky_build_troute ${WORKDIR}/t-route/requirements.txt /tmp/t-route-requirements.txt


################################################################################################################
################################################################################################################
##### Create intermediate Docker build stage for building framework in Rocky Linux environment
FROM pre_ngen_build_routing_${NGEN_WITH_ROUTING} AS rocky_build_ngen

ARG REPO_URL
ARG BRANCH
ARG COMMIT
ARG REFRESH_BEFORE_BUILD
ARG BUILD_PARALLEL_JOBS

ARG NGEN_BUILD_CONFIG_TYPE
ARG NGEN_WITH_BMI_C
ARG NGEN_WITH_BMI_FORTRAN
ARG NGEN_WITH_PYTHON
ARG NGEN_WITH_NETCDF
ARG NGEN_WITH_ROUTING
ARG NGEN_WITH_UDUNITS
ARG NGEN_UDUNITS_QUIET
ARG NGEN_WITH_SQLITE

ARG NGEN_BMI_ACTIVE_SUBMODULES

ARG BUILD_NGEN_SERIAL
ARG BUILD_NGEN_PARALLEL
ARG BUILD_PARTITIONER
ARG BUILD_NOAH_OWP
ARG BUILD_CFE
ARG BUILD_TOPMODEL
ARG BUILD_PET
ARG BUILD_SLOTH

ENV BOOST_ROOT=${WORKDIR}/boost

USER root
RUN if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then \
        chgrp -R ${USER} /usr/local/lib*/python3.* ; \
        chmod -R g+sw /usr/local/lib*/python3.* ; \
    fi
USER ${USER}

ENV VIRTUAL_ENV=/dmod/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python3 -m venv $VIRTUAL_ENV && pip3 install numpy

RUN cd ${BOOST_ROOT} \
    && tar -xf boost_tarball.blob --strip 1 \
    && rm boost_tarball.blob \
    && cd ${WORKDIR}/ngen \
    &&  if [ -z "${COMMIT:-}" ]; then \
            if [ "${REFRESH_BEFORE_BUILD:-}" = "true" ] ; then  \
                git fetch ; \
                git pull --ff-only ; \
                git submodule update --init --depth 1 test/googletest ; \
                git submodule update --init --recursive --depth 1 ; \
            fi ; \
        fi \
    # C++ functionality isn't separate, so always build the test_bmi_cpp shared lib \
    && ./build_sub extern/test_bmi_cpp \
    &&  if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then \
            pip3 install --no-cache-dir -r extern/test_bmi_py/requirements.txt; \
            if [ "${NGEN_WITH_ROUTING}" == "on" ] ; then \
                pip3 install --no-cache-dir /tmp/t-route-wheels/*.whl netCDF4==1.6.3; \
            fi; \
        fi \
    && if [ "${BUILD_NGEN_SERIAL}" == "true" ]; then \
        cmake -B cmake_build_serial -S . \
            -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE} \
            -DNGEN_WITH_MPI:BOOL=OFF \
            -DNGEN_WITH_NETCDF:BOOL=${NGEN_WITH_NETCDF} \
            -DNGEN_WITH_BMI_C:BOOL=${NGEN_WITH_BMI_C} \
            -DNGEN_WITH_BMI_FORTRAN:BOOL=${NGEN_WITH_BMI_FORTRAN} \
            -DNGEN_WITH_PYTHON:BOOL=${NGEN_WITH_PYTHON} \
            -DNGEN_WITH_ROUTING:BOOL=${NGEN_WITH_ROUTING} \
            -DNGEN_WITH_UDUNITS:BOOL=${NGEN_WITH_UDUNITS} \
            -DUDUNITS_QUIET:BOOL=${NGEN_UDUNITS_QUIET} \
            -DNGEN_WITH_SQLITE=${NGEN_WITH_SQLITE} \
            -DCMAKE_INSTALL_PREFIX=/dmod \
            -DNETCDF_INCLUDE_DIR=/usr/include \
            -DNETCDF_LIBRARY=/usr/lib/libnetcdf.so \
            -DNETCDF_CXX_INCLUDE_DIR=/usr/local/include \
            -DNETCDF_CXX_LIBRARY=/usr/local/lib64/libnetcdf-cxx4.so ; \
    fi \
    && if [ "${BUILD_NGEN_PARALLEL}" == "true" ]; then \
        cmake -B cmake_build_parallel -S . \
            -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE} \
            -DNGEN_WITH_MPI:BOOL=ON \
            -DNGEN_WITH_NETCDF:BOOL=${NGEN_WITH_NETCDF} \
            -DNGEN_WITH_BMI_C:BOOL=${NGEN_WITH_BMI_C} \
            -DNGEN_WITH_BMI_FORTRAN:BOOL=${NGEN_WITH_BMI_FORTRAN} \
            -DNGEN_WITH_PYTHON:BOOL=${NGEN_WITH_PYTHON} \
            -DNGEN_WITH_ROUTING:BOOL=${NGEN_WITH_ROUTING} \
            -DNGEN_WITH_UDUNITS:BOOL=${NGEN_WITH_UDUNITS} \
            -DUDUNITS_QUIET:BOOL=${NGEN_UDUNITS_QUIET} \
            -DNGEN_WITH_SQLITE=${NGEN_WITH_SQLITE} \
            -DCMAKE_INSTALL_PREFIX=/dmod \
            -DNETCDF_INCLUDE_DIR=/usr/include \
            -DNETCDF_LIBRARY=/usr/lib/libnetcdf.so \
            -DNETCDF_CXX_INCLUDE_DIR=/usr/local/include \
            -DNETCDF_CXX_LIBRARY=/usr/local/lib64/libnetcdf-cxx4.so ; \
    fi \
    && ln -s $(if [ "${BUILD_NGEN_PARALLEL}" == "true" ]; then echo "cmake_build_parallel"; else echo "cmake_build_serial"; fi) cmake_build \
    &&  if [ "${BUILD_NGEN_PARTITIONER}" == "true" ]; then \
            cmake --build cmake_build --target partitionGenerator -- -j ${BUILD_PARALLEL_JOBS}; \
            $BUILD_DIR/test/test_bmi_python; \
        fi \
    && for BUILD_DIR in $(if [ "${BUILD_NGEN_PARALLEL}" == "true" ]; then echo "cmake_build_parallel"; fi) $(if [ "${BUILD_NGEN_SERIAL}" == "true" ]; then echo "cmake_build_serial"; fi) ; do \
        cmake --build $BUILD_DIR --target ngen -- -j ${BUILD_PARALLEL_JOBS} \
        #Run the tests, if they fail, the image build fails \
        && cmake --build $BUILD_DIR --target test_unit -- -j ${BUILD_PARALLEL_JOBS} \
        && $BUILD_DIR/test/test_unit \
        # C++ functionality isn't separate, so always build and run the test_bmi_cpp testing target \
        && cmake --build $BUILD_DIR --target test_bmi_cpp -- -j ${BUILD_PARALLEL_JOBS} \
        && $BUILD_DIR/test/test_bmi_cpp \
        # For the external language BMI integrations, conditionally build the test packages/libraries and run tests \
        &&  if [ "${NGEN_WITH_BMI_C}" == "ON" ]; then \
                cmake --build $BUILD_DIR --target test_bmi_c -- -j ${BUILD_PARALLEL_JOBS}; \
                $BUILD_DIR/test/test_bmi_c; \
            fi \
        &&  if [ "${NGEN_WITH_BMI_FORTRAN}" == "ON" ]; then \
                cmake --build $BUILD_DIR --target test_bmi_fortran -- -j ${BUILD_PARALLEL_JOBS}; \
                $BUILD_DIR/test/test_bmi_fortran; \
            fi \
        &&  if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then \
                cmake --build $BUILD_DIR --target test_bmi_python -- -j ${BUILD_PARALLEL_JOBS} ; \
                $BUILD_DIR/test/test_bmi_python; \
            fi \
        &&  if [ "${NGEN_WITH_BMI_C}" == "ON" ] && [ "${NGEN_WITH_BMI_FORTRAN}" == "ON" ] && [ "${NGEN_WITH_PYTHON}" == "ON" ]; then \
                cmake --build $BUILD_DIR --target test_bmi_multi -- -j ${BUILD_PARALLEL_JOBS}; \
                $BUILD_DIR/test/test_bmi_multi; \
            fi ; \
    done \
    && rm -rf ${BOOST_ROOT} \
    && mkdir -p /dmod/bin \
    && chown ${USER} /dmod/bin \
    && mkdir -p /dmod/shared_libs \
    && chown ${USER} /dmod/shared_libs \
    && mkdir -p /dmod/datasets \
    && chown ${USER} /dmod/datasets \
    && if [ "${BUILD_NGEN_PARALLEL}" == "true" ]; then cp -a ${WORKDIR}/ngen/cmake_build_parallel/ngen /dmod/bin/ngen-parallel ; fi \
    && if [ "${BUILD_NGEN_SERIAL}" == "true" ]; then cp -a ${WORKDIR}/ngen/cmake_build_serial/ngen /dmod/bin/ngen-serial ; fi \
    && for d in ${NGEN_BMI_ACTIVE_SUBMODULES:?List of active BMI git submodules not defined}; do \
            if [ -d ${WORKDIR}/ngen/extern/${d}/cmake_build ]; then \
                cp -a ${WORKDIR}/ngen/extern/${d}/cmake_build/*.so* /dmod/shared_libs/.; \
            elif [ -d ${WORKDIR}/ngen/extern/${d}/${d}/cmake_build ]; then \
                cp -a ${WORKDIR}/ngen/extern/${d}/${d}/cmake_build/*.so* /dmod/shared_libs/.; \
            fi; \
        done \
    && cd ${WORKDIR} \
    && if [ "${NGEN_BUILD_CONFIG_TYPE:?}" != "Debug" ]; then rm -rf ${WORKDIR}/ngen ; fi

ENV PATH=${WORKDIR}:${WORKDIR}/bin:/dmod/bin:$PATH

################################################################################################################
################################################################################################################
##### A build stage for the partitioner utility image
FROM rocky-ngen-deps as partitioner_image

ARG BUILD_PARALLEL_JOBS
ARG COMMIT
ARG REFRESH_BEFORE_BUILD
ARG NGEN_WITH_BMI_C
ARG NGEN_WITH_BMI_FORTRAN
ARG NGEN_WITH_PYTHON
ARG NGEN_WITH_NETCDF
ARG NGEN_WITH_UDUNITS
ARG NGEN_UDUNITS_QUIET
ARG NGEN_WITH_SQLITE
ARG NGEN_BUILD_CONFIG_TYPE
ARG PARTITIONER_EXECUTABLE

COPY --chown=${USER} partitioner_entrypoint.sh ${WORKDIR}/entrypoint.sh
COPY --chown=${USER} --from=rocky_init_repo ${WORKDIR}/ngen ${WORKDIR}/ngen
ENV BOOST_ROOT=${WORKDIR}/boost

RUN cd ${BOOST_ROOT} \
    && tar -xf boost_tarball.blob --strip 1 \
    && rm boost_tarball.blob \
    && cd ${WORKDIR}/ngen \
    &&  if [ "x$COMMIT" = "x" ]; then \
            if [ "${REFRESH_BEFORE_BUILD:-}" = "true" ] ; then  \
                git pull --ff-only ; \
            fi ; \
        fi \
    && if [ -z "${PARTITIONER_EXECUTABLE:-}" ]; then echo "Error: target/executable name not set" 2>&1 ; exit 1; fi \
    && cmake -B cmake_build -S . \
               -DCMAKE_BUILD_TYPE=${NGEN_BUILD_CONFIG_TYPE} \
               -DNGEN_WITH_MPI:BOOL=OFF \
               -DNGEN_WITH_NETCDF:BOOL=${NGEN_WITH_NETCDF} \
               #-DNGEN_WITH_BMI_C:BOOL=${NGEN_WITH_BMI_C} \
               #-DNGEN_WITH_BMI_FORTRAN:BOOL=${NGEN_WITH_BMI_FORTRAN} \
               #-DNGEN_WITH_PYTHON:BOOL=${NGEN_WITH_PYTHON} \
               #-DNGEN_WITH_ROUTING:BOOL=${NGEN_WITH_ROUTING} \
               -DNGEN_WITH_UDUNITS:BOOL=${NGEN_WITH_UDUNITS} \
               -DUDUNITS_QUIET:BOOL=${NGEN_UDUNITS_QUIET} \
               -DNGEN_WITH_SQLITE=${NGEN_WITH_SQLITE} \
               -DCMAKE_INSTALL_PREFIX=${WORKDIR} \
               -DNETCDF_INCLUDE_DIR=/usr/include \
               -DNETCDF_LIBRARY=/usr/lib/libnetcdf.so \
               -DNETCDF_CXX_INCLUDE_DIR=/usr/local/include \
               -DNETCDF_CXX_LIBRARY=/usr/local/lib64/libnetcdf-cxx4.so \
    && cmake --build cmake_build --target ${PARTITIONER_EXECUTABLE} -- -j ${BUILD_PARALLEL_JOBS} \
    #FIXME remove the data copy, only there for temporary testing \
    && mkdir ${WORKDIR}/bin  \
    && cp cmake_build/${PARTITIONER_EXECUTABLE} ${WORKDIR}/bin \
    && cd ${WORKDIR}  \
    && rm -rf ngen \
    && ls -lah ${BOOST_ROOT} \
    && rm -rf ${BOOST_ROOT} 2>/dev/null \
    && chmod +x ${WORKDIR}/entrypoint.sh

WORKDIR ${WORKDIR}
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib:/usr/local/lib64:/dmod/shared_libs
# This next value is eventually needed for the t-route build ...
# ... make sure it stays in sync with configure step for netcdf above
ENV NETCDFINC=/usr/include
ENV PATH=/dmod/bin:${WORKDIR}:${WORKDIR}/bin:$PATH:/usr/lib64/mpich/bin
ENV NGEN_PART_EXECUTABLE="${PARTITIONER_EXECUTABLE}"
ENTRYPOINT ["entrypoint.sh"]

################################################################################################################
################################################################################################################
##### User customization build stage
FROM rocky_build_ngen as build_customizations

ARG WORKDIR
ARG NGEN_BUILD_CONFIG_TYPE
ENV NGEN_BUILD_CONFIG_TYPE=${NGEN_BUILD_CONFIG_TYPE}

COPY --chown=${USER} --from=pre_build_bmi_iso_c_fortran_dep ${WORKDIR}/iso_c_fortran_bmi ${WORKDIR}/iso_c_fortran_bmi
# Copy libs/data/etc. from various per-module stages
COPY --chown=${USER} --from=build_bmi_sft /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_smp /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_lgar_c /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_sac_sma /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_snow_17 /dmod/ /dmod/
#COPY --from=rocky_build_ngen /dmod/venv /dmod/venv

ENV PATH=${WORKDIR}:${WORKDIR}/bin:/dmod/bin:${PATH}:/usr/lib64/mpich/bin
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib:/usr/local/lib64:/dmod/shared_libs
ENV NETCDFINC=/usr/include
ENV VIRTUAL_ENV=/dmod/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy customization script and any other included artifacts (plus README, to make sure something is always there)
COPY --chown=${USER} customize/* ${WORKDIR}

USER root

# Install packages from a requirements.txt if present
RUN if [ -e ${WORKDIR}/requirements.txt ]; then pip3 install -r ${WORKDIR}/requirements.txt ; fi

# Clone, build, and install simple CMake-buildable repos if the list is present
RUN if [ -e ${WORKDIR}/cmake_repositories.txt ]; then \
        chmod ugo+x ${WORKDIR}/clone_and_cmake_build.sh ; \
        for _REPO_URL in $(cat ${WORKDIR}/cmake_repositories.txt); do \
            ${WORKDIR}/clone_and_cmake_build.sh ${_REPO_URL} ; \
        done ; \
    fi

# If the user script exists and was copied, execute it
RUN if [ -e ${WORKDIR}/customize.sh ]; then chmod ugo+x ${WORKDIR}/customize.sh && ${WORKDIR}/customize.sh ; fi

USER ${USER}

################################################################################################################
################################################################################################################
##### A build stage for testing using the ngen-build-test image
FROM build_customizations as rocky_ngen_build_testing
#FROM rocky-ngen-deps as rocky_ngen_build_testing
#FROM rocky_build_ngen as rocky_ngen_build_testing
#FROM ${DOCKER_INTERNAL_REGISTRY}/ngen-deps:latest as rocky_ngen_build_testing

COPY --chown=${USER} --from=rocky_init_repo ${WORKDIR}/ngen ${WORKDIR}/ngen

ENV BOOST_ROOT=${WORKDIR}/boost

USER root
RUN if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then \
        chgrp -R ${USER} /usr/local/lib*/python3.* ; \
        chmod -R g+sw /usr/local/lib*/python3.* ; \
    fi
USER ${USER}

ENV VIRTUAL_ENV=/dmod/venv
# Don't need this if build_customizations is getting the built /dmod/venv from rocky_build_ngen
#RUN if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then python3 -m venv ${VIRTUAL_ENV} ; fi
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN if [ "${NGEN_WITH_PYTHON}" == "ON" ]; then pip install numpy ; fi

RUN cd ${BOOST_ROOT} && tar -xf boost_tarball.blob --strip 1 && rm boost_tarball.blob
ENV BOOST_ROOT=${WORKDIR}/boost
#COPY --chown=${USER} --from=rocky_build_troute ${WORKDIR}/t-route/wheels /tmp/t-route-wheels
#COPY --chown=${USER} --from=rocky_build_troute ${WORKDIR}/t-route/requirements.txt /tmp/t-route-requirements.txt
WORKDIR ${WORKDIR}/ngen

################################################################################################################
################################################################################################################
##### Software QA/analysis dependencies build stage
FROM build_customizations AS ngen_qa_deps

# Note: *** DO NOT CREATE /dmod/datasets/output AT THIS STAGE !!! (make the user bind mount something in)
# TODO: look at separating things out into individual images a little better, especially the debuginfo-install stuff
USER root
RUN dnf install -y valgrind cppcheck gdb zstd \
    && dnf debuginfo-install -y \
            bzip2-libs-1.0.8-10.el9_5.x86_64 expat-2.5.0-3.el9_5.3.x86_64 glibc-2.34-125.el9_5.8.x86_64 \
            libffi-3.4.2-8.el9.x86_64 libgcc-11.5.0-5.el9_5.x86_64 libgfortran-11.5.0-5.el9_5.x86_64 \
            libquadmath-11.5.0-5.el9_5.x86_64 libstdc++-11.5.0-5.el9_5.x86_64 libuuid-2.37.4-20.el9.x86_64 \
            openssl-libs-3.2.2-6.el9_5.1.x86_64 python3-libs-3.9.21-1.el9_5.x86_64 sqlite-libs-3.34.1-7.el9_3.x86_64 \
            udunits2-2.2.28-5.el9.x86_64 xz-libs-5.2.5-8.el9_0.x86_64 zlib-1.2.11-40.el9.x86_64 \
    && dnf -y clean all \
    && mkdir /dmod/datasets/config \
    && mkdir /dmod/datasets/forcing \
    && mkdir /dmod/datasets/hydrofabric \
    && mkdir -p /dmod/datasets/hydrofabric/ex_geojson_hf_01 \
    && cp -a /ngen/ngen/extern/t-route/test/input/geo/NWM_2.1_Sample_Datasets/Croton_NY_TEST1 /dmod/datasets/hydrofabric/ex_geojson_hf_01/Croton_NY_TEST1 \
    && cp   /ngen/ngen/data/catchment_data.geojson \
            /ngen/ngen/data/nexus_data.geojson \
            /ngen/ngen/extern/t-route/test/input/next_gen/*.json  \
            /dmod/datasets/hydrofabric/ex_geojson_hf_01/ \
    && cp -a /ngen/ngen/data/forcing /dmod/datasets/forcing/test_forcing_01 \
    && chown -R ${USER}:${USER} /dmod/datasets/
USER ${USER}

ARG NGEN_WITH_ROUTING
ENV NGEN_WITH_ROUTING=${NGEN_WITH_ROUTING}

# Copy QA files into place
COPY --chown=${USER} qa /dmod/qa

# For now just use a symlink that we'll set up below
#COPY --chown=${USER} --from=rocky_build_ngen /ngen/ngen/data/bmi /dmod/qa/ngen_ex_bmi_cfgs

# TODO: need to make sure noah-owp parameter files are copied into place, and that configs have that location updated properly

RUN chmod u+x /dmod/qa/run_memcheck.sh \
    && ln -s /ngen/ngen/data/bmi /dmod/qa/ngen_ex_bmi_cfgs

################################################################################################################
################################################################################################################
##### Memcheck specific utility image build stage
FROM ngen_qa_deps AS ngen_memcheck

# For memcheck runs, put some valid-looking param files in place (certainly good enough for this)
COPY --chown=${USER} noah_owp_parameters /dmod/bmi_module_data/noah_owp/parameters/

ENTRYPOINT ["/dmod/qa/run_memcheck.sh"]

################################################################################################################
################################################################################################################
##### CppCheck specific utility image build stage
FROM ngen_qa_deps AS ngen_cppcheck

ARG WORKDIR
ARG CHECK_SRC_DIR="/dmod/qa/c_cpp_sources"

RUN mkdir ${CHECK_SRC_DIR} \
    && cp -a /ngen/ngen ${CHECK_SRC_DIR} \
    && cp -a /ngen/ngen/extern/cfe/cfe ${CHECK_SRC_DIR} \
    && cp -a /ngen/ngen/extern/evapotranspiration/evapotranspiration ${CHECK_SRC_DIR} \
    && cp -a /ngen/ngen/extern/topmodel/topmodel ${CHECK_SRC_DIR} \
    && chmod u+x /dmod/qa/run_cppcheck.sh

COPY --from=build_bmi_sft ${WORKDIR}/SoilFreezeThaw ${CHECK_SRC_DIR}/SoilFreezeThaw
COPY --from=build_bmi_smp ${WORKDIR}/SoilMoistureProfiles ${CHECK_SRC_DIR}/SoilMoistureProfiles
COPY --from=build_bmi_lgar_c ${WORKDIR}/lgar-c ${CHECK_SRC_DIR}/lgar-c

ENTRYPOINT ["/dmod/qa/run_cppcheck.sh"]

################################################################################################################
################################################################################################################
##### General software QA/analysis image build stage
FROM ngen_qa_deps AS ngen_qa

# TODO: consider whether you should change this
ENTRYPOINT ["/bin/bash"]


################################################################################################################
################################################################################################################
##### Model exec ngen worker image build stage
#FROM rocky_build_ngen AS ngen_worker
FROM rocky-base AS ngen_worker

COPY --from=build_customizations / /

ARG NGEN_BMI_ACTIVE_SUBMODULES
ARG DATASET_DIRECTORIES
ARG WORKDIR

ENV WORKDIR=${WORKDIR}
ENV HYDRA_HOST_FILE=/etc/opt/hosts
ENV PATH=${WORKDIR}:${WORKDIR}/bin:/dmod/bin:${PATH}:/usr/lib64/mpich/bin

ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib:/usr/local/lib64:/dmod/shared_libs
# This next value is eventually needed for the t-route build ...
# ... make sure it stays in sync with configure step for netcdf above
ENV NETCDFINC=/usr/include
ENV VIRTUAL_ENV=/dmod/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#RUN cd ./ngen && mkdir ${WORKDIR}/bin && cp cmake_build/ngen ${WORKDIR}/bin && cp -r data ${WORKDIR}/data \
#    && cd $WORKDIR && rm -rf ngen boost

# Copy libs/data/etc. from various per-module stages
COPY --chown=${USER} --from=build_bmi_sft /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_smp /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_lgar_c /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_sac_sma /dmod/ /dmod/
COPY --chown=${USER} --from=build_bmi_snow_17 /dmod/ /dmod/

#  Copy libs data, etc. from customize layer
COPY --chown=${USER} --from=build_customizations /dmod/ /dmod/

USER root
COPY --from=build_customizations /usr/include/ /usr/include/
COPY --from=build_customizations /usr/lib/ /usr/lib/
COPY --from=build_customizations /usr/lib64/ /usr/lib64/


# TODO: (later) consider something like this in the future (at least optionally) when downloading the mc client below:
# ARG MINIO_CLIENT_RELEASE="RELEASE.2024-07-08T20-59-24Z"
# ...
# https://dl.min.io/client/mc/release/linux-amd64/archive/mc.${MINIO_CLIENT_RELEASE}

# Setup minio client; also update path and make sure dataset directory is there
RUN OS_NAME=$(uname -s | tr '[:upper:]' '[:lower:]') \
    && PLATFORM=$(uname -m | tr '[:upper:]' '[:lower:]') \
    && case "${PLATFORM:?}" in \
        aarch64) \
            MINIO_HW_NAME=arm64 \
            ;; \
        x86_64) \
            MINIO_HW_NAME=amd64 \
            ;; \
        *) \
            MINIO_HW_NAME=${PLATFORM} \
            ;; \
    esac \
    && curl -L -o /dmod/bin/mc https://dl.min.io/client/mc/release/${OS_NAME}-${MINIO_HW_NAME}/mc \
    && chmod +x /dmod/bin/mc \
    && mkdir /dmod/.mc \
    && echo "export PATH=${PATH}" >> /etc/profile \
    && sed -i "s/PasswordAuthentication yes/#PasswordAuthentication yes/g" /etc/ssh/sshd_config \
    && sed -i "s/PermitRootLogin yes/PermitRootLogin no/g" /etc/ssh/sshd_config \
    && sed -i "s/#ClientAliveInterval.*/ClientAliveInterval 60/" /etc/ssh/sshd_config \
    && sed -i "s/#ClientAliveCountMax.*/ClientAliveCountMax 5/" /etc/ssh/sshd_config \
    && if [ -f /var/run/nologin ]; then rm /var/run/nologin ; fi ;
USER ${USER}

COPY --chown=${USER} noah_owp_parameters /dmod/bmi_module_data/noah_owp/parameters/
COPY --chown=${USER} ngen_entrypoint.sh /dmod/bin/ngen_entrypoint.sh
COPY --chown=${USER} funcs.sh /dmod/bin/
COPY --chown=${USER} --chmod=744 py_funcs.py /dmod/bin/py_funcs

ENV HYDRA_PROXY_RETRY_COUNT=5

# Change permissions for default entrypoint, make sure it's used if no entrypoint is present, and make sure data volume mount and dataset symlink parent directories exists
RUN chmod +x /dmod/bin/ngen_entrypoint.sh \
    && if [ ! -e /dmod/bin/entrypoint.sh ]; then ln -s /dmod/bin/ngen_entrypoint.sh /dmod/bin/entrypoint.sh ; fi \
    && for p in datasets local_volumes cluster_volumes; do for d in ${DATASET_DIRECTORIES}; do mkdir -p /dmod/${p}/${d}; done; done \
    && pushd /dmod/bin \
    # NOTE use of `ln -sf`. \
    && ( ( stat ngen-parallel && ln -sf ngen-parallel ngen ) || ( stat ngen-serial && ln -sf ngen-serial ngen ) ) \
    && popd

WORKDIR ${WORKDIR}
ENV PATH=${WORKDIR}:$PATH
ENTRYPOINT ["entrypoint.sh"]
CMD [""]

################################################################################################################
################################################################################################################
##### Calibration ngen-cal worker image build stage
FROM ngen_worker AS ngen_cal_worker

ARG NGEN_CAL_BRANCH
ARG NGEN_CAL_COMMIT

# Overwrite the ngen entrypoint script from the parent stage, which is already set up with ENTRYPOINT
COPY --chown=${USER:?} ngen_cal_entrypoint.sh /dmod/bin/ngen_cal_entrypoint.sh

USER root
# Try NGEN_CAL_COMMIT, if not set or empty, use NGEN_CAL_BRANCH
RUN pip3 install --no-cache-dir "git+https://github.com/noaa-owp/ngen-cal@${NGEN_CAL_COMMIT:-${NGEN_CAL_BRANCH}}#egg=ngen_cal&subdirectory=python/ngen_cal"

# Give a way to provide a specific entrypoint, but use default if not provided 
# (though remove a symlink to default ngen worker entrypoint if that's what is in place)
USER ${USER}
RUN chmod +x /dmod/bin/ngen_cal_entrypoint.sh \
    && if [ "$(readlink /dmod/bin/entrypoint.sh)" == "/dmod/bin/ngen_entrypoint.sh" ]; then rm /dmod/bin/entrypoint.sh ; fi \
    && if [ ! -e /dmod/bin/entrypoint.sh ]; then ln -s /dmod/bin/ngen_cal_entrypoint.sh /dmod/bin/entrypoint.sh ; fi

