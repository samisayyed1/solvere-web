#!/usr/bin/env bash
{ echo "PWD=$PWD"; echo "HOME=$HOME"; id; env | sort; } > scaffold-env.txt 2>&1
