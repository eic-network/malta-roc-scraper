#!/usr/bin/env bash

# Run the gatherer script
python3 gather.py;

mkdir output;

# Run the lookup script until the script finishes running succesfully
while [ $? -ne 0 ]; do
    python3 lookup.py;
done;
