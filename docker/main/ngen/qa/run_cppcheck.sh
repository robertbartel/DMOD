#!/bin/bash

# TODO: ************* do something analogous (but for different languages) for artifacts that aren't in C/C++

# TODO: then do much the same thing with trufflehog

#NGEN_CPPCHECK_OUTPUT_FILE=

## Adding --xml will configure for XML output

## Use --force to check all configs/ifdefs
#cppcheck \
#    --enable=performance,portability,missingInclude \
#    --force \
#    --platform=unix64 \
#    --std=c++14 \
#    --output-file=${NGEN_CPPCHECK_OUTPUT_FILE:?ngen cppcheck output file not set} # TODO \
#    -i ngen/ngen/extern # TODO: ignore this \
#    -i ngen/ngen/test/googletest \
#    ngen/ngen

python /dmod/qa/cppcheck_utils.py