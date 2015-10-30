#!/bin/bash

SENSORNUMBER=$1
SENSORTYPE=$2
LINES=$3
INFILE=$4
OUTFILE=$5

if [[ ( "$SENSORTYPE" = "t" ) && ( "$LINES" != "0" ) ]]; then
	awk -v num=$SENSORNUMBER '$3 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "t" ) && ( "$LINES" = "0" ) ]]; then
	awk -v num=$SENSORNUMBER '$3 == num' $INFILE | tee $OUTFILE 1> /dev/null
fi

if [[ ( $SENSORTYPE = "ht" ) && ( "$LINES" != "0" ) ]]; then
    awk -v num=$SENSORNUMBER '$5 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "ht" ) && ( "$LINES" = "0" ) ]]; then
	awk -v num=$SENSORNUMBER '$5 == num' $INFILE | tee $OUTFILE 1> /dev/null
fi

if [[ ( $SENSORTYPE = "co2" ) && ( "$LINES" != "0" ) ]]; then
    awk -v num=$SENSORNUMBER '$3 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "co2" ) && ( "$LINES" = "0" ) ]]; then
	awk -v num=$SENSORNUMBER '$3 == num' $INFILE | tee $OUTFILE 1> /dev/null
fi

if [[ ( $SENSORTYPE = "press" ) && ( "$LINES" != "0" ) ]]; then
    awk -v num=$SENSORNUMBER '$5 == num' $INFILE | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "press" ) && ( "$LINES" = "0" ) ]]; then
	awk -v num=$SENSORNUMBER '$5 == num' $INFILE | tee $OUTFILE 1> /dev/null
fi
