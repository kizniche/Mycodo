#!/bin/sh

SENSORNUMBER=$1
LINES=$2
INFILE=$3
OUTFILE=$4

awk -v num=$SENSORNUMBER '$10 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null