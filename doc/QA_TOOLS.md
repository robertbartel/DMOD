[comment]: <> (TODO: Document qa_builds.sh script)
[comment]: <> (TODO: Document the different memcheck built-in tests cases)

# QA Tips and Suggestions

## Build Without Full DMOD Setup
The [/scripts/qa_builds.sh](../scripts/qa_builds.sh) script can help with building ngen-related images - including those [listed below](#qa-docker-images) - without needing a full deployment configuration for DMOD.  That would be necessary to directly use the DMOD tools for building images.  

A user should be able to clone the repo and immediately run, e.g., `qa_builds.sh ngen ngen-cppcheck` and be able to build those Docker images without performing any DMOD configuration steps.  This will also prevent the DMOD Docker Swarm networks from being unnecessarily initialized.

## Core Dumps in Docker Containers
Sometime ngen can crash, resulting in a core dump.  To be able to access the core dump when running in a container, a few extra options need to be added to the Docker command for running an image:  `--user root --ulimit core=-1 -v /var/lib/systemd/coredump/:/var/lib/systemd/coredump/`.

E.g.:

```shell
docker run --rm -t -i --user root --ulimit core=-1 -v /var/lib/systemd/coredump/:/var/lib/systemd/coredump/ --entrypoint /bin/bash 127.0.0.1:5000/ngen-qa:latest
```

### Host-Specific Core Dump Config
Note that the specific mounted directory will depend on the host system location and where it puts/how it handles core dumps.  Generally, the container has to use the same config as the host.  For a (or at least my) default systemd setup, this means the directories need to align between container and host.  


### Compressed Core Dump Files
In the event that you find core dumps being compressed (systemd seemed to do that for me by default), the `zstd` package is installed in the _ngen-qa_ image.  So you should be able to do something like:
```shell

zstd --decompress /var/lib/systemd/coredump/<core_dump_file>.zst
```


# QA Docker Images

> [!NOTE]
> Below, the registry value for images is always `127.0.0.1:5000`.  This is the default.  The `DOCKER_INTERNAL_REGISTRY` variable can be explicitly set in the environment to control this value.

## Summary
| Build Service                   | Image Name                            | Purpose                                                                                                                        |                                                                                                                   
|---------------------------------|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| [ngen-cppcheck](#ngen-cppcheck) | `127.0.0.1:5000/ngen-cppcheck:latest` | Run CppCheck static analysis on relevant or provided codes.                                                                    | 
| [ngen-memcheck](#ngen-memcheck) | `127.0.0.1:5000/ngen-memcheck:latest` | Run ngen configurations through Valgrind Memcheck (see [this README.md](../docker/main/ngen/qa/realization_configs/README.md). | 
| [ngen-qa](#ngen-qa)             | `127.0.0.1:5000/ngen-qa:latest`       | General image for ngen and module QA and debugging.                                                                            | 

---
## ngen-cppcheck
The `127.0.0.1:5000/ngen-cppcheck:latest` image will run static analysis on C/C++ codes using CppCheck.  By default, it will run on the ngen source code and the published OWP BMI modules bundled into the DMOD ngen images, if the module is written in either C or C++. 

It is possible to bind mount a directory at `/dmod/qa/users_sources`, and instead have the subdirectories within analyzed.  Note also that any tar archives within this user-provided directory will be automatically extracted.

### Entrypoint
The entrypoint runs a dedicated script (currently no args) that runs CppCheck either on a set of pre-configured source codes (ngen, cfe, SFT, etc.) or subdirectories of `/dmod/qa/users_sources` directory (which only exists if the user bind-mounts it into the container).

### Usage Requirements
* A volume, or more typically a host directory, must be mounted to `/dmod/datasets/output/` so that output can be accessible.

```bash
docker run --rm -t -i -v $(pwd)/qa_out:/dmod/datasets/output 127.0.0.1:5000/ngen-cppcheck:latest
```
---
## ngen-memcheck

The `127.0.0.1:5000/ngen-memcheck:latest` image will run a few preset ngen configurations through Valgrind Memcheck (see [this README.md](../docker/main/ngen/qa/realization_configs/README.md) for details).

### Entrypoint
The entrypoint runs a dedicated script (currently no args) that runs a set of pre-built ngen configurations through Memcheck.

### Usage Requirements
* A volume, or more typically a host directory, must be mounted to `/dmod/datasets/output/` so that output can be accessible

### Suggestions

* It is often good to add the [options for handling core dumps](#core-dumps-in-docker-containers).

### Usage Example

```bash
docker run --rm -t -i -v $(pwd)/qa_out:/dmod/datasets/output 127.0.0.1:5000/ngen-memcheck:latest
```
---
## ngen-qa
The `127.0.0.1:5000/ngen-qa:latest` is a general image that builds ngen and other items for debugging, and includes various tools for analysis and debugging such as Valgrind, GDB, CppCheck, debugging symbols for dependencies, etc.

### Suggestions

* It is often good to add the [options for handling core dumps](#core-dumps-in-docker-containers).
* Even if full options to handle new core dumps aren't used, the directory can be mounted to allow access to existing core dumps for debugging through GDB.

### Usage Example

```bash
docker run --rm -t -i -v /var/lib/systemd/coredump/:/var/lib/systemd/coredump/ --entrypoint /bin/bash 127.0.0.1:5000/ngen-qa:latest
```


