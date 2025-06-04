#!/bin/bash


ulimit -n 1024

python /dmod/qa/memcheck_utils.py "${@}"