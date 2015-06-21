#!/bin/bash
# createHDR.sh
# Version 1.4.1 (October 4 2010)
# Author: Vincent Tassy <photo@tassy.net>
# Site: http://linuxdarkroom.tassy.net
# This script is released under a CC-GNU GPL License

# A bash script to create an HDR image out of set of jpg or CR2 images
# Results in a Gimp xcf file containing 3 layers
#	an exposure blend of the original images using enfuse
#	a tone-mapped image using the mantiuk06 operator
#	a tone-mapped image using the fattal02 operator

# This script is based on the work of Edu Pérez - http://photoblog.edu-perez.com

# Changelog
#
# Version 1.0
#	first public release
# Version 1.1
#	- using pfsoutimgmagick instead of pfsout/pfsouttiff because they are broken in Fedora 11
# Version 1.2
#	- changed header to user /bin/bash instead of /bin/sh to avoid problems on ubuntu
# Version 1.3
#	- added options for ufraw (by Stephane Brette)
#	- added NEF support (by Stephane Brette)
#	- added calibration phase to the HDR generation
# Version 1.3.1
#	- fixed problems with 16 bit support
#	- fixed a problem with ufraw configuration option
# Version 1.3.2
#	- Detects numbers in the folder containing the images and names the HDR file accordingly. Makes it easier to consolidate
#	- added LC_ALL=C to ufraw-batch execution so it accepts x.x number sytax on all systems (by Timo)
#	- Preserve EXIF information in the generated XCF
# Version 1.4
#	- added progression display using kdialog
# Version 1.4.1
#	- fixed some bugs

SELF=`basename $0`	# Ouselve
DIR=""
ALIGN=0			# Don't align the images by default
QUIET=0			# not too quiet by default
USEKDE=0		# command line invocation by default
GAMMA="0.45"		# Default gamma
LINEARITY="0.10"	# Default linearity
EXPOSURE="0.0"		# Default exposure compensation
SATURATION="1.0"	# Default saturation
CONFIGURATION=""
HDRFILEPREFIX="HDR"	# Prefix for the generated Gimp file

displayHelp() {
	echo "Create an HDR picture out of a set of bracketed images."
	echo "Based on the work of Edu Pérez - http://photoblog.edu-perez.com"
	echo
	echo "Usage: $SELF [OPTION] DIR"
	echo -e "  -a\t\tAlign the pictures first"
	echo -e "  -g{val} \tgamma option for RAW conversion (--gamma={val} -- DEFAULT=0.45)"
	echo -e "  -s{val} \tsaturation option for RAW conversion (--saturation={val} -- DEFAULT=1.0)"
	echo -e "  -e{val} \texposure compensation option for RAW conversion (--exposure={val} -- DEFAULT=0.0)"
	echo -e "  -l{val} \tlinearity option for RAW conversion (--linearity={val} -- DEFAULT=0.10)"
	echo -e "  -c{path} \tConfiguration file for ufrraw IDFILE.ufraw"
	echo -e "  -q\t\tQuiet"
	echo -e "  -k\t\tDisplay progress information with kdialog"
	echo -e "  -h\t\tThis help"
	echo
	echo "Report bugs to <photo@tassy.net>"
}

# test params
while getopts aqkhg:l:e:s:c: argument
do
        case $argument in
                a)ALIGN=1;;
                q)QUIET=1;;
		k)USEKDE=1;;
                h)displayHelp;exit;;
                g)GAMMA=$OPTARG;;
		l)LINEARITY=$OPTARG;;
		e)EXPOSURE=$OPTARG;;
		s)SATURATION=$OPTARG;;
		c)CONFIGURATION=$OPTARG;;
        esac
done
shift $(($OPTIND-1))
DIR=$1
if [ $USEKDE = 1 ]; then
	QUIET=1
fi
if [ -z $DIR ]; then
	displayHelp
	exit
fi
if [ ! -d "$DIR" ]; then
	echo "$DIR is not a valid directory"
	displayHelp
	exit
fi
DIR=$(cd "$DIR" && pwd) #transform to absolute path
# Check of the directory contains only one type of files
if [ `find $DIR -maxdepth 1 -type f -exec basename {} \; | sed "s/.*\.//g" | tr '[:lower:]' '[:upper:]' | sort -u | wc -l` != 1 ]; then
	if [ $USEKDE = 1 ]; then
		kdialog --title createHDR --error "Directory contains multiple filetypes"
	else
		echo "Error: Directory contains multiple filetypes"
	fi
	exit
fi

# Check if the directory name ends with a number. If so, append it to the HDR file name
NUMBER=`echo $DIR | sed 's/^.*[^0-9]\([0-9]\+\)$/\1/'`
if [ $DIR = $NUMBER ]; then
	NUMBER=""	
fi
HDRFILE="$HDRFILEPREFIX$NUMBER.xcf"

FILES=(`find $DIR -maxdepth 1 -type f -print | sort`) # List files in the selected directory
filetype=`basename ${FILES[0]} | sed "s/.*\.//g" | tr '[:lower:]' '[:upper:]'` # Get file extension
if [ $filetype = "JPG" ] || [ $filetype = "CR2" ] || [ $filetype = "NEF" ]; then
	if [ $USEKDE = 1 ]; then
		dbusRef=`kdialog --title "createHDR" --progressbar "Parsing EXIF information" 9`
	fi
	if [ $QUIET = 0 ]; then
		echo "Files are $filetype"
		echo "Parsing EXIF information"
	fi
	if [ $filetype = "JPG" ]; then
		jpeg2hdrgen ${FILES[*]} > "$DIR"/pfs.hdrgen # Generate input file for pfstools
		JPEGFILENAME=${FILES[0]} # We'll use the first file to provide the EXIF info in the generated XCF
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 2
	fi
	else
		dcraw2hdrgen ${FILES[*]} > "$DIR"/pfs.hdrgen # Generate input file for pfstools
		if [ $USEKDE = 1 ]; then
			qdbus $dbusRef Set "" "value" 1
			qdbus $dbusRef setLabelText "Developing RAW files"
		fi
		if [ $filetype = "CR2" ]; then
			if [ $QUIET = 0 ]; then
				echo "Devloping RAW files"
			fi
			if [ -z $CONFIGURATION ]; then
				LC_ALL=C; ufraw-batch --wb=camera --gamma=$GAMMA --linearity=$LINEARITY --exposure=$EXPOSURE --saturation=$SATURATION --out-type=tiff --out-depth=16 --overwrite ${FILES[*]} 2>/dev/null
			else
				LC_ALL=C; ufraw-batch --conf=$CONFIGURATION --out-type=tiff --out-depth=16 --overwrite ${FILES[*]} 2>/dev/null
			fi
			# Also Generate a JPEG of the first image so as to save the EXIF metadata and embed it in the generated XCF
			LC_ALL=C; ufraw-batch --wb=camera --gamma=$GAMMA --linearity=$LINEARITY --exposure=$EXPOSURE --saturation=$SATURATION --out-type=jpeg --compression=97 --overwrite --output=${FILES[0]%.*}.jpg ${FILES[0]} 2>/dev/null
			FILES=("$DIR"/*.tif)
		else
			if [ $QUIET = 0 ]; then
				echo "Devloping RAW files"
			fi
			if [ -z $CONFIGURATION ]; then
				LC_ALL=C; ufraw-batch --wb=camera --gamma=$GAMMA --exposure=$EXPOSURE --saturation=$SATURATION --out-type=tiff --out-depth=16 --overwrite ${FILES[*]} 2>/dev/null
			else
				LC_ALL=C; ufraw-batch --conf=$CONFIGURATION --out-type=tiff --out-depth=16 --overwrite ${FILES[*]} 2>/dev/null
			fi
			# Also Generate a JPEG of the first image so as to save the EXIF metadata and embed it in the generated XCF
			LC_ALL=C; ufraw-batch --wb=camera --gamma=$GAMMA --exposure=$EXPOSURE --saturation=$SATURATION --out-type=jpeg --compression=97 --overwrite --output=${FILES[0]%.*}.jpg ${FILES[0]} 2>/dev/null
			FILES=("$DIR"/*.tif)
		fi
		JPEGFILENAME=${FILES[0]%.*}.jpg # This is the name of the generated JPEG file to be used to preserve the EXIF metadata in the generated XCF
		if [ $USEKDE = 1 ]; then
			qdbus $dbusRef Set "" "value" 2
		fi
	fi
	if [ $ALIGN = 1 ]; then
		if [ $QUIET = 0 ]; then
			echo "Aligning images"
		fi
		if [ $USEKDE = 1 ]; then
			qdbus $dbusRef setLabelText "Aligning images"
		fi
		align_image_stack -a "$DIR"/AIS_ ${FILES[*]} >/dev/null 2>&1
		FILES=("$DIR"/AIS_*.tif)
		if [ $USEKDE = 1 ]; then
			qdbus $dbusRef Set "" "value" 3
		fi
	fi
	if [ $QUIET = 0 ]; then
		echo "Generating Enfused image"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Generating Enfused image"
	fi
	enfuse -o "$DIR"/enfuse.tif ${FILES[*]} >/dev/null 2>&1
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 4
	fi
	if [ $QUIET = 0 ]; then
		echo "Generating HDR"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Generating HDR"
	fi
	i=0
	cat "$DIR"/pfs.hdrgen | while read LINE; do
		echo "${FILES[$i]} $LINE" | cut -d' ' -f1,3- >> "$DIR"/pfs_updated.hdrgen # Keep meta-data but change files involved
		let "i = $i +1"
	done
	if [ $filetype = "JPG" ]; then
		pfsinhdrgen "$DIR"/pfs_updated.hdrgen | pfshdrcalibrate -c none -r gamma | pfsclamp --rgb | pfsout "$DIR"/pfs.hdr 2>/dev/null # Generate HDR image
	else
		pfsinhdrgen "$DIR"/pfs_updated.hdrgen | pfshdrcalibrate -c none -r gamma --bpp 16 | pfsclamp --rgb | pfsout "$DIR"/pfs.hdr 2>/dev/null # Generate HDR image
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 5
	fi
	if [ $QUIET = 0 ]; then
		echo "Tone-mapping with mantiuk06 operator"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Tone-mapping with mantiuk06 operator"
	fi
	# Tonemap using mantiuk06
	pfsin "$DIR"/pfs.hdr | pfstmo_mantiuk06 -e 1 -s 1 2>/dev/null | pfsgamma --gamma 2.2 | pfsoutimgmagick "$DIR"/hdr_mantiuk06.tif >/dev/null 2>&1
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 6
	fi
	if [ $QUIET = 0 ]; then
		echo "Tone-mapping with fattal02 operator"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Tone-mapping with fattal02 operator"
	fi
	# Tonemap using fattal02
	pfsin "$DIR"/pfs.hdr | pfstmo_fattal02 -s 1 | pfsgamma --gamma 2.2 | pfsoutimgmagick "$DIR"/hdr_fattal02.tif 
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 7
	fi
	if [ $QUIET = 0 ]; then
		echo "Creating image stack"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Creating image stack"
	fi
	# Stack the generated images in Gimp
	gimp -c -d -i -f -s -n -b \
		'(define (create-hdr-stack jpegfilename enfusefilename mantiukfilename fattalfilename targetfilename)
		(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE jpegfilename jpegfilename)))
		(jpeglayer (car (gimp-image-get-active-layer image)))
		(enfuselayer (car (gimp-file-load-layer RUN-NONINTERACTIVE image enfusefilename)))
		(mantiuklayer (car (gimp-file-load-layer RUN-NONINTERACTIVE image mantiukfilename)))
		(fattallayer (car (gimp-file-load-layer RUN-NONINTERACTIVE image fattalfilename))))
		(gimp-image-add-layer image enfuselayer -1)
		(gimp-image-add-layer image mantiuklayer -1)
		(gimp-layer-set-mode mantiuklayer SOFTLIGHT-MODE)
		(gimp-layer-set-opacity mantiuklayer 50.0)
		(gimp-image-add-layer image fattallayer -1)
		(gimp-layer-set-mode fattallayer OVERLAY-MODE)
		(gimp-image-remove-layer image jpeglayer)
		(gimp-xcf-save RUN-NONINTERACTIVE image fattallayer targetfilename targetfilename)
		(gimp-image-delete image)))

		(create-hdr-stack "'$JPEGFILENAME'" "'$DIR/enfuse.tif'" "'$DIR/hdr_mantiuk06.tif'" "'$DIR/hdr_fattal02.tif'" "'$DIR/$HDRFILE'")
		(gimp-quit 0)' >/dev/null 2>&1
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 8
	fi
	if [ $QUIET = 0 ]; then
		echo "Cleaning up"
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef setLabelText "Cleaning up"
	fi
	rm -f $DIR/*.tif $DIR/pfs.hdr $DIR/pfs.hdrgen $DIR/pfs_updated.hdrgen
	if [ $filetype != "JPG" ]; then
		rm -f $DIR/$JPEGFILENAME
	fi
	if [ $USEKDE = 1 ]; then
		qdbus $dbusRef Set "" "value" 9
		qdbus $dbusRef close
	fi
else
	if [ $USEKDE = 1 ]; then
		kdialog --title createHDR --error "Unsupported file type: $filetype"
	else
		echo "Unsupported file type: $filetype"
	fi
fi
