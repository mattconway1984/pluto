#!/bin/bash

abort()
{
    # An error was trapped, cause the build to fail by returning no zero
    exit 1
}
trap 'abort' 0
set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
INPUT_DIR="$PROJECT_DIR/protodefs"
PROTODEF_FILE="$INPUT_DIR/delegator.proto"
PROTODEF_PATCH="$INPUT_DIR/delegator.patch"
OUTPUT_DIR="$PROJECT_DIR/pluto/delegator/protobuf"

# Ensure the output directory exists
mkdir -p $OUTPUT_DIR

# Generate the GRPC files:
python -m grpc_tools.protoc \
    -I$INPUT_DIR \
    --python_out=$OUTPUT_DIR \
    --grpc_python_out=$OUTPUT_DIR \
    $PROTODEF_FILE

# GRPC is not generating the import path correctly, so there is a patch to apply:
patch -t $OUTPUT_DIR/delegator_pb2_grpc.py < $PROTODEF_PATCH

trap : 0
