/* MycoDo - Regulate temperature and humidity with raspberryPi and DHT22 sensor
   To compile: gcc mycodo-1.0.c -I/usr/local/include -L/usr/local/lib -lwiringPi -o mycodo
   To execute: sudo mycodo `sudo /var/www/bin/mycodo-sense.py -d`
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wiringPi.h>
#include <time.h>
#include <limits.h>

// Relay1 HEPA Pin - wiringPi pin 4 is BCM_GPIO 23, GPIO4
// Relay2 HUMI Pin - wiringPi pin 3 is BCM_GPIO 22, GPIO3
// Relay3 CFAN Pin - wiringPi pin 1 is BCM_GPIO 18, GPIO1
// Relay4 HEAT Pin - wiringPi pin 0 is BCM_GPIO 17, GPIO0

#define RHepa 1
#define RHum  2
#define RFan  3
#define RHeat 4
#define SIZE 256

int RHepat[] = {0, 10, 20, 30, 40, 50};
int RHumt[] = {0, 5, 10, 15, 20, 30};
int RFant[] = {0, 10, 20, 30, 40, 50};
int RHeatt[] = {0, 5, 15, 20, 45, 50};

int year;
int month;
int day;
int hour;
int min;
int sec;
int timestampL;
double hum;
double temp;
float wfactor = 2.2;

char line[256];
int linenum = 0;
char sonTemp[256], soffTemp[256], shighTemp[256], sonHum[256], soffHum[256], sweboverride[256], stempState[256], shumState[256];
int highTemp = 80;
int offTemp = 60;
int onTemp = 10;
int offHum = 40;
int onHum = 10;
int weboverride = 0;
int tempState = 2;
int humState = 2;

int main( int argc, char *argv[] )
{
	if (!argc)
	{
		printf("Missing input argument!\n");
		return 1;
	}

	if (wiringPiSetup() == -1)
	{
		printf("wiringPiSetup returned -1!\n");
		return 1;
	}

	readStates();

	year = atoi(argv[1]);
	month  = atoi(argv[2]);
	day  = atoi(argv[3]);
	hour  = atoi(argv[4]);
	min  = atoi(argv[5]);
	sec  = atoi(argv[6]);
	timestampL = atoi(argv[7]);
	hum = atof(argv[8]);
	temp = atof(argv[10]);

	printf("Sensors Read: %s-%s-%s %s:%s:%s %i\n", argv[1], argv[2], argv[3], argv[4], argv[5], argv[6], timestampL);

	printf("Temperature: %.1f  Range: (%i - %i) %.1f degrees from offTemp. ", temp, onTemp, offTemp, offTemp - temp);
	CheckTemp();

	printf("Humidity:    %.1f  Range: (%i - %i) %.1f percent from offHum. ", hum, onHum, offHum, offHum - hum);
	CheckHum();

	writeStates();

	if (!weboverride) { ChangeRelays ( offTemp - temp, offHum - hum ); }
	else { printf("WebOverride activated - No relay change!\n"); }

	return 0;
}


int readStates (void)
{
	linenum = 0;
	FILE * pFile;
	pFile = fopen ("/var/www/graph/PiConfig" , "r");
	while(fgets(line, 256, pFile) != NULL)
	{
		linenum++;
		if(line[0] == '#') continue;

		if(sscanf(line, "%s %s %s %s %s %s %s %s", sonTemp, soffTemp, shighTemp, sonHum, soffHum, sweboverride, stempState, shumState) != 8)
		{
			fprintf(stderr, "Config file syntax error\n", linenum);
			continue;
		}
		printf("\nonTemp offTemp highTemp onHum offHum WebOverride tempState humState\n%s %s %s %s %s %s %s %s\n", sonTemp, soffTemp, shighTemp, sonHum, soffHum, sweboverride, stempState, shumState);
	}

	onTemp = atoi(sonTemp);
	offTemp = atoi(soffTemp);
	highTemp = atoi(shighTemp);
	onHum = atoi(sonHum);
	offHum = atoi(soffHum);
	weboverride = atoi(sweboverride);
	tempState = atoi(stempState);
	humState = atoi(shumState);

	fclose(pFile);
	return 0;
}


int writeStates (void)
{
	FILE * pFile;
	pFile = fopen ("/var/www/graph/PiConfig" , "w");
	if (pFile == NULL) {
		printf("Couldn't open PiConfig for writing.\n");
		return 1;
	}

	if (!pFile)
		perror("fopen");

	fprintf(pFile, "%d %d %d %d %d %d %d %d\n", onTemp, offTemp, highTemp, onHum, offHum, weboverride, tempState, humState);
	fclose(pFile);
	return 0;
}

int CheckTemp (void)
{
	if ( temp < onTemp ) 
	{
		tempState = 1;
		printf("< threshhold. Heat On.\n");
	}
	else if ( temp >= onTemp && temp >= offTemp && temp < highTemp )
	{
		tempState = 2;
		printf(">= threshhold. Heat off until < onTemp.\n");
	}
	else if ( temp >= highTemp )
	{
		tempState = 3;
		printf("> highTemp. Heat Off, All fans On.\n");
	}
	else
	{
		printf("Leaving on until > offTemp or off until < onTemp.\n");
	}
	return 0;
}


int CheckHum (void)
{
	if ( hum < onHum )
	{
		humState = 1;
		printf("< threshhold. Hum On.\n");
	}
	else if ( hum >= onHum && hum >= offHum )
	{
		humState = 2;
		printf(">= threshhold. Hum Off until < onHum.\n");
	}
	else
	{
		printf("Leaving on until > offHum or off until < onHum.\n");
	}
	return 0;
}

int ChangeRelays (double tdiff, double hdiff)
{
	if ( tdiff < -2 && tdiff >= -4 ) RFant[0] = 1;
	else if ( tdiff < -4 && tdiff >= -6 ) RFant[0] = 2;
	else if ( tdiff < -6 && tdiff >= -8 ) RFant[0] = 3;
	else if ( tdiff < -8 && tdiff >= -10 ) RFant[0] = 4;
	else RFant[0] = 5;

	if ( tdiff <= 0.5 ) RHeatt[0] = 1;
	else if ( tdiff <= 1 ) RHeatt[0] = 2;
	else if ( tdiff <= 2 ) RHeatt[0] = 3;
	else if ( tdiff <= 3 ) RHeatt[0] = 4;
	else RHeatt[0] = 5;

	if ( hdiff < 5 ) RHumt[0] = 1;
	else if ( hdiff < 10 ) RHumt[0] = 2;
	else if ( hdiff < 15 ) RHumt[0] = 3;
	else if ( hdiff < 20 ) RHumt[0] = 4;
	else RHumt[0] = 5;

	char Tcom[120];
	sprintf(Tcom, "/var/www/bin/mycodo-relay.sh %d %d &", RHeat, RHeatt[RHeatt[0]]);
	char Hcom[120];
	sprintf(Hcom, "/var/www/bin/mycodo-relay.sh %d %d &", RHum, RHumt[RHumt[0]]);
	char Pcom[120];
	sprintf(Pcom, "/var/www/bin/mycodo-relay.sh %d %d &", RHepa, RFant[RFant[0]]);
	char Fcom[120];

	// tempState 1=below offTemp 2=above offTemp now cooling 3=too high turn all fans on
	// humState  1=below offHum  2=above offHum now cooling
	// RHepa 1, RHum  2, RFan  3, RHeat 4

	if ( tempState == 1 && humState == 1 )
	{
		printf("Heat on %d sec, Hepa fan off, Humidifier on %d sec, Circulatory fan on %d sec.\n", RHeatt[RHeatt[0]], RHumt[RHumt[0]], RHeatt[RHeatt[0]]);
		digitalWrite (RHepa, 0);
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/bin/mycodo-relay.sh %d %d &", RFan, RHeatt[RHeatt[0]]);
		system(Fcom);
		sleep(1);
		system(Tcom);
		if( RHeatt[RHeatt[0]] >= RHumt[RHumt[0]] ) {
			printf("Waiting %d seconds.\n", (int)(RHeatt[RHeatt[0]] * wfactor) );
			sleep( (int)(RHeatt[RHeatt[0]] * wfactor) );
		}
		else {
			printf("Waiting %d seconds.\n", (int)(RHumt[RHumt[0]] * wfactor) );
			sleep( (int)(RHumt[RHumt[0]] * wfactor) );
		}
	}
	else if ( tempState == 2 && humState == 1 )
	{
		printf("Heat off, Hepa fan off, Humidifier on %d sec, Circulatory fan on %d sec.\nWaiting %d seconds.\n", RHumt[RHumt[0]], (int)(RHumt[RHumt[0]] * wfactor) );
		digitalWrite (RHepa, 0);
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/bin/mycodo-relay.sh %d %d &", RFan, RHumt[RHumt[0]]);
		system(Fcom);
		digitalWrite (RHeat, 0);
		sleep( (int)(RHumt[RHumt[0]] * wfactor) );
	}
	else if ( tempState == 3 && humState == 1 )
	{
		printf("Heat off, Hepa fan on %d sec, Humidifier on %d sec, Circulatory fan on %d sec.\n", RHepat[RHepat[0]], RHumt[RHumt[0]], RHumt[RHumt[0]] + 10);
		system(Pcom);
		sleep(1);
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/bin/mycodo-relay.sh %d %d &", RFan, RHumt[RHumt[0]] + 10);
		system(Fcom);
		digitalWrite (RHeat, 0);
		if( RHepat[RHepat[0]] >= RHumt[RHumt[0]] ) {
			printf("Waiting %d seconds.\n", (int)(RHepat[RHepat[0]] * wfactor) );
			sleep( (int)(RHepat[RHepat[0]] * wfactor) );
		}
		else {
			printf("Waiting %d seconds.\n", (int)(RHumt[RHumt[0]] * wfactor) );
			sleep( (int)(RHumt[RHumt[0]] * wfactor) );
		}
	}
	else if ( tempState == 3 && humState == 2 )
	{
		printf("Heat off, Hepa fan on %d sec, Humidifier off, Circulatory fan on %d sec.\n", RHepat[RHepat[0]], RFant[RFant[0]]);
		system(Pcom);
		digitalWrite (RHum, 0);
		sleep(1);
		sprintf(Fcom, "/var/www/bin/mycodo-relay.sh %d %d &", RFan, RFant[RFant[0]]);
		system(Fcom);
		digitalWrite (RHeat, 0);
		if( RHepat[RHepat[0]] >= RFant[RFant[0]] ) {
			printf("Waiting %d seconds.\n", (int)(RHepat[RHepat[0]] * wfactor) );
			sleep( (int)(RHepat[RHepat[0]] * wfactor) );
		}
		else {
			printf("Waiting %d seconds.\n", (int)(RFant[RFant[0]] * wfactor) );
			sleep( (int)(RFant[RFant[0]] * wfactor) );
		}
	}
	else if ( tempState == 1 && humState == 2 )
	{
		printf("Heat on %d sec, Hepa fan off, Humidifier off, Circulatory fan on %d sec.\n", RHeatt[RHeatt[0]], RHeatt[RHeatt[0]]);
		printf("Waiting %d seconds.\n", (int)(RHeatt[RHeatt[0]] * wfactor) );
		digitalWrite (RHepa, 0);
		digitalWrite (RHum, 0);
		sprintf(Fcom, "/var/www/bin/mycodo-relay.sh %d %d &", RFan, RHeatt[RHeatt[0]]);
		//system(Fcom);
		sleep(1);
		system(Tcom);
		sleep( (int)(RHeatt[RHeatt[0]] * wfactor) );
	}
	else if ( ((tempState == 2 || tempState == 3) && (humState == 2 || humState == 3)) )
	{
		printf("Waiting 40 seconds.\n");
		digitalWrite (RHeat, 0);
		digitalWrite (RHepa, 0);
		digitalWrite (RHum, 0);
		digitalWrite (RFan, 0);
		sleep ( 40 );
	}
	else printf("Something went wrong!\n");
	return 0;
}

