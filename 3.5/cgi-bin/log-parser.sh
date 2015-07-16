#!/bin/sh

SENSORNUMBER=$1
SENSORTYPE=$2
LINES=$3
INFILE=$4
OUTFILE=$5

if [ $SENSORTYPE = "ht" ]; then
    awk -v num=$SENSORNUMBER '$10 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
fi

if [ $SENSORTYPE = "co2" ]; then
    awk -v num=$SENSORNUMBER '$8 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
fi