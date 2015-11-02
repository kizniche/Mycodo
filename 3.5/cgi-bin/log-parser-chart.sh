#!/bin/bash

SENSORNUMBER=$1
SENSORTYPE=$2
LINES=$3
INFILE1=$4
INFILE2=$5
OUTFILE=$6

if [[ ( "$SENSORTYPE" = "all" ) ]]; then
	cat $INFILE1 $INFILE2 | sed -e "s/^/$SENSORNUMBER /" | tee $OUTFILE 1> /dev/null
fi

if [[ ( "$SENSORTYPE" = "relay" ) ]]; then
	cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
fi

if [[ ( "$SENSORTYPE" = "t" ) && ( "$SENSORNUMBER" = "x" ) ]]; then
	cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "t" ) && ( "$LINES" != "0" ) ]]; then
	cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "t" ) && ( "$LINES" = "0" ) ]]; then
	cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | tee $OUTFILE 1> /dev/null
fi

if [[ ( "$SENSORTYPE" = "ht" ) && ( "$SENSORNUMBER" = "x" ) ]]; then
	cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
elif [[ ( $SENSORTYPE = "ht" ) && ( "$LINES" != "0" ) ]]; then
    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "ht" ) && ( "$LINES" = "0" ) ]]; then
	cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | tee $OUTFILE 1> /dev/null
fi

if [[ ( "$SENSORTYPE" = "co2" ) && ( "$SENSORNUMBER" = "x" ) ]]; then
	cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
elif [[ ( $SENSORTYPE = "co2" ) && ( "$LINES" != "0" ) ]]; then
    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "co2" ) && ( "$LINES" = "0" ) ]]; then
	cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | tee $OUTFILE 1> /dev/null
fi

if [[ ( "$SENSORTYPE" = "press" ) && ( "$SENSORNUMBER" = "x" ) ]]; then
	cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
elif [[ ( $SENSORTYPE = "press" ) && ( "$LINES" != "0" ) ]]; then
    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | tail -n -$LINES | tee $OUTFILE 1> /dev/null
elif [[ ( "$SENSORTYPE" = "press" ) && ( "$LINES" = "0" ) ]]; then
	cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | tee $OUTFILE 1> /dev/null
fi
