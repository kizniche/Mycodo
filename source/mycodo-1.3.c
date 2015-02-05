/* MycoDo - Regulate temperature and humidity with raspberryPi and DHT22 sensor
   To compile: gcc mycodo-1.0.c -I/usr/local/include -L/usr/local/lib -lconfig -lwiringPi -o mycodo
   To change relays: sudo mycodo `sudo /var/www/mycodo/mycodo-sense.py -d`
   To write config: sudo mycodo w [onTemp] [offTemp] [highTemp] [onHum] [offHum] [webOR] [tempState] [humState]
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wiringPi.h>
#include <time.h>
#include <limits.h>
#include <libconfig.h>

// Main configuration file
char *config_file_name = "/var/www/mycodo/mycodo.conf";

// Relay1 HEPA Pin - wiringPi pin 4 is BCM_GPIO 23, GPIO4
// Relay2 HUMI Pin - wiringPi pin 3 is BCM_GPIO 22, GPIO3
// Relay3 CFAN Pin - wiringPi pin 1 is BCM_GPIO 18, GPIO1
// Relay4 HEAT Pin - wiringPi pin 0 is BCM_GPIO 17, GPIO0

#define RHepa 1
#define RHum  2
#define RFan  3
#define RHeat 4
#define SIZE 256

// Number of seconds to turn on 
float RHeats[] = {0.3, 0.8, 1.5, 2};
int RHeatt[] = {0, 10, 27, 35, 43, 55};
int RHums[] = {5, 10, 15, 20};
int RHumt[] = {0, 5, 10, 15, 20, 30};
int RFans[] = {-2, -4, -6, -8, -10};
int RFant[] = {0, 10, 20, 30, 40, 50};
int RHepat[] = {0, 10, 20, 30, 40, 50};
float wfactor = 2;

int year;
int month;
int day;
int hour;
int min;
int sec;
int timestampL;
double hum;
double temp;

int highTemp = 80;
int offTemp = 60;
int onTemp = 10;
int offHum = 40;
int onHum = 10;
int webOR = 0;
int tempState = 2;
int humState = 2;

int main( int argc, char *argv[] )
{
	if (!argc)
	{
		printf("Missing input argument!\n");
		return 1;
	}

	// write input to config file - for web php control interface
	if (strcmp(argv[1], "w") == 0) {
		onTemp = atoi(argv[2]);
		offTemp =  atoi(argv[3]);
		highTemp =  atoi(argv[4]);
		onHum =  atoi(argv[5]);
		offHum =  atoi(argv[6]);
		webOR =  atoi(argv[7]);
		tempState =  atoi(argv[8]);
		humState =  atoi(argv[9]);
		writeCfg();
	}

	// read config file and print only variable values to screen
	else if (strcmp(argv[1], "r") == 0) {
		readCfg();
		printf("%i %i %i %i %i %i %i %i\n", onTemp, offTemp, highTemp, onHum, offHum, webOR, tempState, humState);
	}

	else {
		// convert string input to int
		year = atoi(argv[1]);
		month  = atoi(argv[2]);
		day  = atoi(argv[3]);
		hour  = atoi(argv[4]);
		min  = atoi(argv[5]);
		sec  = atoi(argv[6]);
		timestampL = atoi(argv[7]);
		hum = atof(argv[8]);
		temp = atof(argv[9]);

		// read config file and set variables
		printf("\n%s:%s:%s %i Read config file %s",  argv[4], argv[5], argv[6], timestampL, config_file_name);
		readCfg();
		printf("\nonTemp: %i, offTemp: %i, highTemp: %i, onHum: %i, offHum: %i, webOR: %i, tempState: %i, humState: %i", onTemp, offTemp, highTemp, onHum, offHum, webOR, tempState, humState);
		printf("\n%s:%s:%s %i Read sensors", argv[4], argv[5], argv[6], timestampL);
		if ( tempState == 2 ) printf("\nTemperature: %.1f  Range: (%i - %i) %.1f deg. from onTemp. ", temp, onTemp, offTemp, temp - onTemp);
		else printf("\nTemperature: %.1f  Range: (%i - %i) %.1f deg. from offTemp. ", temp, onTemp, offTemp, offTemp - temp);

		// read temperature sensor
		CheckTemp();

                if ( humState == 2 ) printf("\nHumidity:    %.1f  Range: (%i - %i) %.1f%% from onHum. ", hum, onHum, offHum, hum - onHum);
		else printf("\nHumidity:    %.1f  Range: (%i - %i) %.1f%% from offHum. ", hum, onHum, offHum, offHum - hum);
		CheckHum();

		if (!webOR) { ChangeRelays ( offTemp - temp, offHum - hum ); }
		else { 
			printf("\nWebOverride activated - No relay change!");
			printf("\nWaiting 60 seconds.\n");
                	sleep ( 60 );
		}
	}

	return 0;
}


int readCfg (void)
{
	config_t cfg;
	config_init(&cfg);

	/* Read the file. If there is an error, report it and exit. */
	if (!config_read_file(&cfg, config_file_name))
	{
		printf("\n%s:%d - %s", config_error_file(&cfg), config_error_line(&cfg), config_error_text(&cfg));
		config_destroy(&cfg);
		return -1;
	}

	if (!config_lookup_int(&cfg, "onTemp", &onTemp))  printf("\nNo 'onTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "offTemp", &offTemp)) printf("\nNo 'offTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "highTemp", &highTemp)) printf("\nNo 'highTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "onHum", &onHum)) printf("\nNo 'onHum' setting in configuration file.");
	if (!config_lookup_int(&cfg, "offHum", &offHum)) printf("\nNo 'offHum' setting in configuration file.");
	if (!config_lookup_int(&cfg, "webOR", &webOR)) printf("\nNo 'webOR' setting in configuration file.");
	if (!config_lookup_int(&cfg, "tempState", &tempState)) printf("\nNo 'tempState' setting in configuration file.");
	if (!config_lookup_int(&cfg, "humState", &humState)) printf("\nNo 'humState' setting in configuration file.");

	config_destroy(&cfg);

	return 0;
}

int writeCfg (void)
{
	config_t cfg;
	config_setting_t *tonTemp = 0;
	config_setting_t *toffTemp = 0;
	config_setting_t *thighTemp = 0;
	config_setting_t *tonHum = 0;
	config_setting_t *toffHum = 0;
	config_setting_t *twebOR = 0;
	config_setting_t *ttempState = 0;
	config_setting_t *thumState = 0;

	config_init(&cfg);

	if (!config_read_file(&cfg, config_file_name))
	{
		printf("\n%s:%d - %s", config_error_file(&cfg), config_error_line(&cfg), config_error_text(&cfg));
		config_destroy(&cfg);
		return -1;
	}

	/* lookup variables in config file */
	tonTemp = config_lookup(&cfg, "onTemp");
	toffTemp = config_lookup(&cfg, "offTemp");
	thighTemp = config_lookup(&cfg, "highTemp");
	tonHum = config_lookup(&cfg, "onHum");
	toffHum = config_lookup(&cfg, "offHum");
	twebOR = config_lookup(&cfg, "webOR");
	ttempState = config_lookup(&cfg, "tempState");
	thumState = config_lookup(&cfg, "humState");

	/* get variables from config file then print the variables that changed */
	if (config_setting_get_int(tonTemp) != onTemp) {
		printf("\nonTemp: %i -> ", config_setting_get_int(tonTemp));
		config_setting_set_int(tonTemp, onTemp);
		printf("%i", config_setting_get_int(tonTemp));
	}

	if (config_setting_get_int(toffTemp) != offTemp) {
		printf("\noffTemp: %i -> ", config_setting_get_int(toffTemp));
		config_setting_set_int(toffTemp, offTemp);
		printf("%i", config_setting_get_int(toffTemp));
	}

	if (config_setting_get_int(thighTemp) != highTemp) {
		printf("\nhighTemp: %i -> ", config_setting_get_int(thighTemp));
		config_setting_set_int(thighTemp, highTemp);
		printf("%i", config_setting_get_int(thighTemp));
	}

	if (config_setting_get_int(tonHum) != onHum) {
		printf("\nonHum: %i -> ", config_setting_get_int(tonHum));
		config_setting_set_int(tonHum, onHum);
		printf("%i", config_setting_get_int(tonHum));
	}

	if (config_setting_get_int(toffHum) != offHum) {
		printf("\noffHum: %i -> ", config_setting_get_int(toffHum));
		config_setting_set_int(toffHum, offHum);
		printf("%i", config_setting_get_int(toffHum));
	}

	if (config_setting_get_int(twebOR) != webOR) {
		printf("\nwebOR: %i -> ", config_setting_get_int(twebOR));
		config_setting_set_int(twebOR, webOR);
		printf("%i", config_setting_get_int(twebOR));
	}

	if (config_setting_get_int(ttempState) != tempState) {
		printf("\ntempState: %i -> ", config_setting_get_int(ttempState));
		config_setting_set_int(ttempState, tempState);
		printf("%i", config_setting_get_int(ttempState));
	}

	if (config_setting_get_int(thumState) != humState) {
		printf("\nhumState: %i -> ", config_setting_get_int(thumState));
		config_setting_set_int(thumState, humState);
		printf("%i", config_setting_get_int(thumState));
	}

	/* write the modified config file */
	config_write_file(&cfg, config_file_name);

	config_destroy(&cfg);

	return 0;
}

int CheckTemp (void)
{
	if ( temp < onTemp ) 
	{
		tempState = 1;
		printf("< threshhold. Heat On.");
	}
	else if ( temp >= onTemp && temp >= offTemp && temp < highTemp)
	{
		tempState = 2;
		printf(">= threshhold. Heat off until < onTemp.");
	}
	else if ( temp >= highTemp )
	{
		tempState = 3;
		printf("> highTemp. Heat Off, All fans On.");
	}
	else
	{
		if ( tempState == 2 ) printf("Leaving off until < onTemp.");
		else printf("Leaving on until > offTemp.");
		return;
	}

	writeCfg();	

	return 0;
}


int CheckHum (void)
{
	if ( hum < onHum )
	{
		humState = 1;
		printf("< threshhold. Hum On.");
	}
	else if ( hum >= onHum && hum >= offHum )
	{
		humState = 2;
		printf(">= threshhold. Hum Off until < onHum.");
	}
	else
	{
		if ( humState == 2 ) printf("Leaving off until < onHum.");
		else printf("Leaving on until > offHum.");
		return 0;
	}

	writeCfg();

	return 0;
}

int ChangeRelays (double tdiff, double hdiff)
{
	if ( tdiff < RFans[0] && tdiff >= RFans[1] ) RFant[0] = 1;
	else if ( tdiff < RFans[1] && tdiff >= RFans[2] ) RFant[0] = 2;
	else if ( tdiff < RFans[2] && tdiff >= RFans[3] ) RFant[0] = 3;
	else if ( tdiff < RFans[3] && tdiff >= RFans[4] ) RFant[0] = 4;
	else RFant[0] = 5;

	if ( tdiff <= RHeats[0] ) RHeatt[0] = 1;
	else if ( tdiff <= RHeats[1] ) RHeatt[0] = 2;
	else if ( tdiff <= RHeats[2] ) RHeatt[0] = 3;
	else if ( tdiff <= RHeats[3] ) RHeatt[0] = 4;
	else RHeatt[0] = 5;

	if ( hdiff < RHums[0] ) RHumt[0] = 1;
	else if ( hdiff < RHums[1] ) RHumt[0] = 2;
	else if ( hdiff < RHums[2] ) RHumt[0] = 3;
	else if ( hdiff < RHums[3] ) RHumt[0] = 4;
	else RHumt[0] = 5;

	char Tcom[120];
	sprintf(Tcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHeat, RHeatt[RHeatt[0]]);
	char Hcom[120];
	sprintf(Hcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHum, RHumt[RHumt[0]]);
	char Pcom[120];
	sprintf(Pcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHepa, RFant[RFant[0]]);
	char Fcom[120];

	// tempState 1=below offTemp 2=above offTemp now cooling 3=too high turn all fans on
	// humState  1=below offHum  2=above offHum now cooling
	// RHepa 1, RHum  2, RFan  3, RHeat 4

	if ( tempState == 1 && humState == 1 )
	{
		printf("\nHeat on %d sec, Hepa fan off, Humidifier on %d sec, Circulatory fan on %d sec.", RHeatt[RHeatt[0]], RHumt[RHumt[0]], RHeatt[RHeatt[0]]);
		system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RFan, RHeatt[RHeatt[0]]);
		system(Fcom);
		sleep(1);
		system(Tcom);
		if( RHeatt[RHeatt[0]] >= RHumt[RHumt[0]] ) {
			printf("\nWaiting %d seconds.\n", (int)(RHeatt[RHeatt[0]] * wfactor) );
			sleep( (int)(RHeatt[RHeatt[0]] * wfactor) );
		}
		else {
			printf("\nWaiting %d seconds.\n", (int)(RHumt[RHumt[0]] * wfactor) );
			sleep( (int)(RHumt[RHumt[0]] * wfactor) );
		}
	}
	else if ( tempState == 2 && humState == 1 )
	{
		printf("\nHeat off, Hepa fan off, Humidifier on %d sec, Circulatory fan on %d sec.\nWaiting %d seconds.\n", RHumt[RHumt[0]], (int)(RHumt[RHumt[0]] * wfactor) );
		system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RFan, RHumt[RHumt[0]]);
		system(Fcom);
		system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
		sleep( (int)(RHumt[RHumt[0]] * wfactor) );
	}
	else if ( tempState == 3 && humState == 1 )
	{
		printf("\nHeat off, Hepa fan on %d sec, Humidifier on %d sec, Circulatory fan on %d sec.", RHepat[RHepat[0]], RHumt[RHumt[0]], RHumt[RHumt[0]] + 10);
		system(Pcom);
		sleep(1);
		system(Hcom);
		sleep(1);
		sprintf(Fcom, "/var/www/mycdo/mycodo-relay.sh %d %d &", RFan, RHumt[RHumt[0]] + 10);
		system(Fcom);
		system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
		if( RHepat[RHepat[0]] >= RHumt[RHumt[0]] ) {
			printf("\nWaiting %d seconds.\n", (int)(RHepat[RHepat[0]] * wfactor) );
			sleep( (int)(RHepat[RHepat[0]] * wfactor) );
		}
		else {
			printf("\nWaiting %d seconds.\n", (int)(RHumt[RHumt[0]] * wfactor) );
			sleep( (int)(RHumt[RHumt[0]] * wfactor) );
		}
	}
	else if ( tempState == 3 && humState == 2 )
	{
		printf("\nHeat off, Hepa fan on %d sec, Humidifier off, Circulatory fan on %d sec.", RHepat[RHepat[0]], RFant[RFant[0]]);
		system(Pcom);
		system("/var/www/mycodo/mycodo-relay.sh 2 0 &");
		sleep(1);
		sprintf(Fcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RFan, RFant[RFant[0]]);
		system(Fcom);
		system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
		if( RHepat[RHepat[0]] >= RFant[RFant[0]] ) {
			printf("\nWaiting %d seconds.\n", (int)(RHepat[RHepat[0]] * wfactor) );
			sleep( (int)(RHepat[RHepat[0]] * wfactor) );
		}
		else {
			printf("\nWaiting %d seconds.\n", (int)(RFant[RFant[0]] * wfactor) );
			sleep( (int)(RFant[RFant[0]] * wfactor) );
		}
	}
	else if ( tempState == 1 && humState == 2 )
	{
		printf("\nHeat on %d sec, Hepa fan off, Humidifier off, Circulatory fan on %d sec.", RHeatt[RHeatt[0]], RHeatt[RHeatt[0]]);
		printf("\nWaiting %d seconds.\n", (int)(RHeatt[RHeatt[0]] * wfactor) );
		system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
		system("/var/www/mycodo/mycodo-relay.sh 2 0 &");
		sprintf(Fcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RFan, RHeatt[RHeatt[0]]);
		//system(Fcom);
		sleep(1);
		system(Tcom);
		sleep( (int)(RHeatt[RHeatt[0]] * wfactor) );
	}
	else if ( ((tempState == 2 || tempState == 3) && (humState == 2 || humState == 3)) )
	{
		printf("\nWaiting 60 seconds.\n");
		system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
		system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
		system("/var/www/mycodo/mycodo-relay.sh 2 0 &");
		//system("/var/www/mycodo/mycodo-relay.sh 3 0 &");
		sleep ( 60 );
	}
	else printf("Something went wrong!\n");
	return 0;
}

