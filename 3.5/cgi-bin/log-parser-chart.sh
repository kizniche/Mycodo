#!/bin/bash

SENSORNUMBER=$1
SENSORTYPE=$2
TIMESTART=$3
TIMEEND=$4
INFILE1=$5
INFILE2=$6
OUTFILE=$7

if [[ ( "$SENSORTYPE" = "all" ) ]]; then
	if [[ ( "$TIMESTART" = "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | sed -e "s/^/$SENSORNUMBER /" | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | sed -e "s/^/$SENSORNUMBER /" | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | sed -e "s/^/$SENSORNUMBER /" | tee $OUTFILE 1> /dev/null
	fi
fi

if [[ ( "$SENSORTYPE" = "relay" ) ]]; then
	if [[ ( "$TIMESTART" = "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
	fi
fi

if [[ ( "$SENSORNUMBER" = "x" ) ]]; then
	if [[  ( "$TIMESTART" = "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		echo $TIMESTART
		echo $TIMEEND
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tee $OUTFILE 1> /dev/null
	elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
		cat $INFILE1 $INFILE2 | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
	fi
else
	if [[ ( "$SENSORTYPE" = "t" ) ]]; then
		if [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
			cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tail -n -$LINES | tee $OUTFILE 1> /dev/null
		elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
			cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
		fi
	fi
	if [[ ( "$SENSORTYPE" = "ht" ) ]]; then
		if [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tee $OUTFILE 1> /dev/null
		elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
			cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
		fi
	fi
	if [[ ( "$SENSORTYPE" = "co2" ) ]]; then

		if [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tee $OUTFILE 1> /dev/null
		elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
			cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$3 == num' | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
		fi
	fi

	if [[ ( "$SENSORTYPE" = "press" ) ]]; then
		if [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" != "0" ) ]]; then
		    cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | awk -v timestart="$TIMESTART" -v timeend="$TIMEEND" -F, '{ if ($1>timestart && $1<timeend) print }' | tee $OUTFILE 1> /dev/null
		elif [[ ( "$TIMESTART" != "0" ) && ( "$TIMEEND" = "0" ) ]]; then
			cat $INFILE1 $INFILE2 | awk -v num=$SENSORNUMBER '$5 == num' | awk -v timestart="$TIMESTART" -F, '{ if ($1>timestart) print }' | tee $OUTFILE 1> /dev/null
		fi
	fi
fi
