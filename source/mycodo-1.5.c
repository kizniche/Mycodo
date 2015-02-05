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

// Contratints of relay control
// If difference between actual temp/hum and set temp/hum is equal or below Xs
// turn on heater/humidifier for Xt seconds, then leave off for 

// Heater outside chamber
float RHeats[] = {0.3, 0.8, 1.5, 2};
int RHeatt[] = {0, 30, 30, 30, 30, 30};
int RHeato[] = {0, 300, 275, 250, 225, 200};
int RHeatTS = 0;

int RHums[] = {5, 10, 15, 20};
int RHumt[] = {0, 45, 45, 45, 45, 45};
int RHumo[] = {0, 60, 60, 60, 60, 60};
int RHumTS = 0;

int RFans[] = {-2, -4, -6, -8, -10};
int RFant[] = {0, 120, 180, 240, 300, 360};
int RFano[] = {0, 220, 221, 222, 223, 224};
int RFanTS = 0;

int RHepat[] = {0, 10, 20, 30, 40, 50};
int RHepao[] = {0, 20, 30, 40, 50, 55};
int RHepaTS = 0;

/* Heater inside chamber
   float RHeats[] = {0.3, 0.8, 1.5, 2};
   int RHeatt[] = {0, 10, 27, 35, 43, 55};
   int RHeato[] = {60, 60, 60, 60, 60};
   int RHums[] = {5, 10, 15, 20};
   int RHumt[] = {0, 5, 10, 15, 20, 30};
   int RHumo[] = {60, 60, 60, 60, 60};
   int RFans[] = {-2, -4, -6, -8, -10};
   int RFant[] = {0, 10, 20, 30, 40, 50};
   int RFano[] = {60, 60, 60, 60, 60};
   int RHepat[] = {0, 10, 20, 30, 40, 50};
 */

double wfactor = 1.0;
int sleept = 60;

int year;
int month;
int day;
int hour;
int min;
int sec;
int timestampL;
double hum;
double temp;

int relay1o = 0;
int relay2o = 0;
int relay3o = 0;
int relay4o = 0;

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

	/*  */
	if (!config_lookup_int(&cfg, "onTemp", &onTemp))  printf("\nNo 'onTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "offTemp", &offTemp)) printf("\nNo 'offTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "highTemp", &highTemp)) printf("\nNo 'highTemp' setting in configuration file.");
	if (!config_lookup_int(&cfg, "onHum", &onHum)) printf("\nNo 'onHum' setting in configuration file.");
	if (!config_lookup_int(&cfg, "offHum", &offHum)) printf("\nNo 'offHum' setting in configuration file.");
	if (!config_lookup_int(&cfg, "webOR", &webOR)) printf("\nNo 'webOR' setting in configuration file.");
	if (!config_lookup_int(&cfg, "tempState", &tempState)) printf("\nNo 'tempState' setting in configuration file.");
	if (!config_lookup_int(&cfg, "humState", &humState)) printf("\nNo 'humState' setting in configuration file.");
	if (!config_lookup_int(&cfg, "RHeatTS", &RHeatTS)) printf("\nNo 'RHeatTS' setting in configuration file.");
	if (!config_lookup_int(&cfg, "RHumTS", &RHumTS)) printf("\nNo 'RHumTS' setting in configuration file.");
	if (!config_lookup_int(&cfg, "RHepaTS", &RHepaTS)) printf("\nNo 'RHepaTS' setting in configuration file.");
	if (!config_lookup_int(&cfg, "RFanTS", &RFanTS)) printf("\nNo 'RFanTS' setting in configuration file.");
	if (!config_lookup_float(&cfg, "wfactor", &wfactor)) printf("\nNo 'wfactor' setting in configuration file.");
	if (!config_lookup_int(&cfg, "relay1o", &relay1o)) printf("\nNo 'relay1o' setting in configuration file.");
	if (!config_lookup_int(&cfg, "relay3o", &relay3o)) printf("\nNo 'relay3o' setting in configuration file.");

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
	config_setting_t *tRHeatTS = 0;
	config_setting_t *tRHumTS = 0;
	config_setting_t *tRHepaTS = 0;
	config_setting_t *tRFanTS = 0;
	config_setting_t *twfactor = 0;
	config_setting_t *trelay1o = 0;
	config_setting_t *trelay3o = 0;

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
	tRHeatTS = config_lookup(&cfg, "RHeatTS");
	tRHumTS = config_lookup(&cfg, "RHumTS");
	tRHepaTS = config_lookup(&cfg, "RHepaTS");
	tRFanTS = config_lookup(&cfg, "RFanTS");
	twfactor = config_lookup(&cfg, "wfactor");
	trelay1o = config_lookup(&cfg, "relay1o");
	trelay3o = config_lookup(&cfg, "relay3o");

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
	if (config_setting_get_int(tRHeatTS) != RHeatTS) {
		printf("\nRHeatTS: %i -> ", config_setting_get_int(tRHeatTS));
		config_setting_set_int(tRHeatTS, RHeatTS);
		printf("%i", config_setting_get_int(tRHeatTS));
	}
	if (config_setting_get_int(tRHumTS) != RHumTS) {
		printf("\nRHumTS: %i -> ", config_setting_get_int(tRHumTS));
		config_setting_set_int(tRHumTS, RHumTS);
		printf("%i", config_setting_get_int(tRHumTS));
	}
	if (config_setting_get_int(tRHepaTS) != RHepaTS) {
		printf("\nRHepaTS: %i -> ", config_setting_get_int(tRHepaTS));
		config_setting_set_int(tRHepaTS, RHepaTS);
		printf("%i", config_setting_get_int(tRHepaTS));
	}
	if (config_setting_get_int(tRFanTS) != RFanTS) {
		printf("\nRFanTS: %i -> ", config_setting_get_int(tRFanTS));
		config_setting_set_int(tRFanTS, RFanTS);
		printf("%i", config_setting_get_int(tRFanTS));
	}
	if (config_setting_get_float(twfactor) != wfactor) {
		printf("\nwfactor: %i -> ", config_setting_get_float(twfactor));
		config_setting_set_float(twfactor, wfactor);
		printf("%i", config_setting_get_float(twfactor));
	}
	if (config_setting_get_int(trelay1o) != relay1o) {
		printf("\nrelay1o: %i -> ", config_setting_get_int(trelay1o));
		config_setting_set_int(trelay1o, relay1o);
		printf("%i", config_setting_get_int(trelay1o));
	}
	if (config_setting_get_int(trelay3o) != relay3o) {
		printf("\nrelay3o: %i -> ", config_setting_get_int(trelay3o));
		config_setting_set_int(trelay3o, relay3o);
		printf("%i", config_setting_get_int(trelay3o));
	}

	/* write the modified config file */
	config_write_file(&cfg, config_file_name);

	config_destroy(&cfg);
	return 0;
}

int CheckTemp (void)
{
	if ( temp < offTemp ) 
	{
		tempState = 1;
		printf("< onTemp. Heat On.");
	}
	else if ( temp >= offTemp && temp < highTemp)
	{
		tempState = 2;
		printf(">= offTemp. Heat off until < offTemp.");
	}
	else if ( temp >= highTemp )
	{
		tempState = 3;
		printf("> highTemp. Heat Off, All fans On.");
	}
	else
	{
		if ( tempState == 2 ) printf("Heat off until < offTemp.");
		else printf("Heat on until > offTemp.");
		return;
	}
	writeCfg();	
	return 0;
}


int CheckHum (void)
{
	if ( hum < offHum )
	{
		humState = 1;
		printf("< offHum. Hum On.");
	}
	else if ( hum >= offHum)
	{
		humState = 2;
		printf(">= offHum. Hum Off until < offHum.");
	}
	else
	{
		if ( humState == 2 ) printf("Leaving off until < offHum.");
		else printf("Leaving on until > offHum.");
		return 0;
	}
	writeCfg();
	return 0;
}

relay1(int i) // HEPA Fan
{
	printf("\nRelay 1 (HEPA): ");
	if (relay1o) {
		switch (i) {
			case 0:
				printf("Off");
				system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
				break;
			case 1:
				printf("Turn on for %d seconds, then off for %d seconds.", RHepat[RHepat[0]], RHepao[RHepat[0]]);
				char Pcom[120];
				sprintf(Pcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHepa, RHepat[RHepat[0]]);
				system(Pcom);
				if (RHepao[RHepat[0]] < sleept) sleept = RHepao[RHepat[0]];
				RHepaTS = timestampL;
				writeCfg();
				break;
			case 2:
				printf("Remaining on for %d more seconds (of %d)", RHepat[RHepao[0]] - (timestampL - RHepaTS), RHepat[RHepao[0]]);
				if ( RHepat[RHepat[0]] - (timestampL - RHepaTS) < sleept) sleept = RHepat[RHepat[0]] - (timestampL - RHepaTS);
				break;
			case 3:
				printf("Off for %d more seconds.", RHepao[RHepat[0]] - (timestampL - RHepaTS));
				system("/var/www/mycodo/mycodo-relay.sh 1 0 &");
				if (RHepao[RHepat[0]] - (timestampL - RHepaTS) < sleept) sleept = RHepao[RHepat[0]] - (timestampL - RHepaTS);
				break;
		}
	}
	else printf("Override");
}

relay2(int i) // Humidifier
{
	printf("\nRelay 2  (Hum): ");
	switch (i) {
		case 0: // Turn relay4 off
			printf("Off until humidity < offHum");
			system("/var/www/mycodo/mycodo-relay.sh 2 0 &");
			break;
		case 1:
			RHumo[0] = RHumt[0];
			printf("Turn on for %d sec, then off for %d seconds.", RHumt[RHumt[0]], RHumo[RHumt[0]]);
			char Hcom[120];
			sprintf(Hcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHum, RHumt[RHumt[0]]);
			system(Hcom);
			if (RHumo[RHumt[0]] < sleept) sleept = RHumo[RHumt[0]];
			RHumTS = timestampL;
			writeCfg();
			break;
		case 2:
			printf("Remaining on for %d more seconds (of %d)", RHumt[RHumt[0]] - (timestampL - RHumTS), RHumt[RHumt[0]]);
			if ( RHumt[RHumt[0]] - (timestampL - RHumTS) < sleept) sleept = RHumt[RHumt[0]] - (timestampL - RHumTS);
			break;
		case 3:
			printf("Off for %d more seconds.", RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS));
			system("/var/www/mycodo/mycodo-relay.sh 2 0 &");
			if (RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS) < sleept) sleept = RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS);
			break;
	}
}

relay3(int i) // Circulatory Fan
{
	printf("\nRelay 3  (Fan): ");
	if (relay3o) {
		switch (i) {
			case 0:
				printf("Off until temperature < offTemp.");
				system("/var/www/mycodo/mycodo-relay.sh 3 0 &");
				break;
			case 1:
				printf("Turn on for %d sec, then off for %d seconds.", RHumt[RHumt[0]], RHumo[RHumt[0]]);
				char Fcom[120];
				sprintf(Fcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RFan, RHumt[RHumt[0]]);
				system(Fcom);
				break;
		}
	}
	else printf("Override");
}

relay4(int i) // Heat
{
	printf("\nRelay 4 (Heat): ");
	switch (i) {
		case 0: // Turn off
			printf("Off until temperature < offTemp.");
			system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
			break;
		case 1: // Turn on
			RHeato[0] = RHeatt[0];
			printf("Turn on for %d sec, then off for %d seconds.", RHeatt[RHeatt[0]], (int)(RHeato[RHeatt[0]]*wfactor));
			char Tcom[120];
			sprintf(Tcom, "/var/www/mycodo/mycodo-relay.sh %d %d &", RHeat, RHeatt[RHeatt[0]]);
			system(Tcom);
			if((int)(RHeato[RHeatt[0]]*wfactor) < sleept) sleept = (int)(RHeato[RHeatt[0]]*wfactor);
			RHeatTS = timestampL;
			writeCfg();
			break;
		case 2: // Leave on
			printf("Remaining on for %d more seconds (of %d)", RHeatt[RHeatt[0]] - (timestampL - RHeatTS), RHeatt[RHeatt[0]]);
			if ( RHeatt[RHeatt[0]] - (timestampL - RHeatTS) < sleept ) sleept = RHeatt[RHeatt[0]] - (timestampL - RHeatTS);
			break;
		case 3:
			printf("Off for %d more seconds.", (int)(RHeato[RHeatt[0]]*wfactor) + RHeatt[RHeatt[0]] - (timestampL - RHeatTS));
			system("/var/www/mycodo/mycodo-relay.sh 4 0 &");
			if ((int)(RHeato[RHeatt[0]]*wfactor) + RHeatt[RHeatt[0]] - (timestampL - RHeatTS) < sleept) sleept = (int)(RHeato[RHeatt[0]]*wfactor) + RHeatt[RHeatt[0]] - (timestampL - RHeatTS);
			break;
	}
}

int ChangeRelays (double tdiff, double hdiff)
{
	if ( tdiff > RFans[0] ) RFant[0] = 1;
	else if ( tdiff > RFans[1] ) RFant[0] = 2;
	else if ( tdiff > RFans[2] ) RFant[0] = 3;
	else if ( tdiff > RFans[3] ) RFant[0] = 4;
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

	// tempState: 1=below offTemp, 2=above offTemp now cooling, 3=too high turn all fans on
	// humState:  1=below offHum,  2=above offHum now cooling
	// Relays: RHepa 1, RHum  2, RFan  3, RHeat 4
	// relayx(Y), Y: 0=Turn off, 1=Turn on, 2=Leave on, 3=Leave off 

	if ( tempState == 1 && humState == 1 ) // Heat on, humidifier on
	{
		// Relay 1 HEPA
		relay1(0); // Turn relay1 off
		usleep(500000);

		// Relay 2 Humidifier
		if (timestampL - RHumTS - RHumt[RHumt[0]] < RHumo[RHumt[0]]) { // If not end of off timer
			if (timestampL - RHumTS < RHumt[RHumt[0]]) { // If not at end of on timer
				relay2(2); // Leave relay2 on
				usleep(500000);
                                relay3(1); // Turn relay3 on
			} else {
				if (RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS) <= 0) {
					relay2(1); // Turn relay2 on
					usleep(500000);
					relay3(1); // Turn relay3 on
				}
				else {
					relay2(3); // Leave relay2 off
					usleep(500000);
					relay3(0); // Turn relay3 off
				}
			}
		} else {
			relay2(1); // Turn relay2 on
			usleep(500000);
			relay3(1); // Turn relay3 on
		}
		usleep(500000);

		// Relay 4 Heater
		if (timestampL - RHeatTS - RHeatt[RHeatt[0]] < (int)(RHeato[RHeatt[0]]*wfactor)) { // If not end of on and off timer
			if (timestampL - RHeatTS < RHeatt[RHeatt[0]]) { // If not at end of on timer
				relay4(2); // Leave relay4 on
			} else {
				if ((int)(RHeato[RHeatt[0]]*wfactor) + RHeatt[RHeatt[0]] - (timestampL - RHeatTS) <= 0) relay4(1); // Turn relay4 on
				else relay4(3); // Leave relay4 off
			}
		} else relay4(1); // Turn relay4 on
	}
	else if ( tempState == 2 && humState == 1 )
	{
		// Relay 1 HEPA
		relay1(0); // Turn relay1 off
		usleep(500000);

		// Relay 2 Humidifier
		if (timestampL - RHumTS - RHumt[RHumt[0]] < RHumo[RHumt[0]]) { // If not end of off timer
			if (timestampL - RHumTS < RHumt[RHumt[0]]) { // If not at end of on timer
				relay2(2); // Leave relay2 on
			} else {
				if (RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS) <= 0) {
					relay2(1); // Turn relay2 on
					usleep(500000);
					relay3(1); // Turn relay3 on
				}
				else {
					relay2(3); // Leave relay2 off
					usleep(500000);
					relay3(0); // Turn relay3 off
				}
			}
		} else {
			relay2(1); // Turn relay2 on
			usleep(500000);
			relay3(1); // Turn relay3 on
		}
		usleep(500000);

		// Relay 4 Heater
		relay4(0); // Turn relay4 off until offTemp reached
	}
	else if ( tempState == 3 && humState == 1 )
	{
		// Relay 1 HEPA
		if (timestampL - RHepaTS < RHepao[RHepat[0]]) { // If not end of off timer
			if (timestampL - RHepaTS < RHepat[RHepat[0]]) { // If not at end of on timer
				relay1(2); // Leave relay1 on
			} else relay1(3); // Leave relay1 off
		} else relay1(1); // Turn relay1 on
		usleep(500000);

		// Relay 2 Humidifier, Relay 3 Circulatory Fan
		if (timestampL - RHumTS - RHumt[RHumt[0]] < RHumo[RHumt[0]]) { // If not end of off timer
			if (timestampL - RHumTS < RHumt[RHumt[0]]) { // If not at end of on timer
				relay2(2); // Leave relay2 on
			} else {
				if (RHumo[RHumt[0]] + RHumt[RHumt[0]] - (timestampL - RHumTS) <= 0) {
					relay2(1); // Turn relay2 on
					usleep(500000);
					relay3(1); // Turn relay3 on
				}
				else {
					relay2(3); // Leave relay2 off
					usleep(500000);
					relay3(0); // Turn relay3 off
				}
			}
		} else {
			relay2(1); // Turn relay2 on
			usleep(500000);
			relay3(1); // Turn relay3 on
		}
		usleep(500000);

		// Relay 4 Heater
		relay4(0); // Turn relay4 off until onTemp reached
	}
	else if ( tempState == 3 && (humState == 2 || humState == 3))
	{
		// Relay 1 HEPA
		if (timestampL - RHepaTS < RHepao[RHepat[0]]) { // If not end of off timer
			if (timestampL - RHepaTS < RHepat[RHepat[0]]) { // If not at end of on timer
				relay1(2); // Leave relay1 on
			} else relay1(3); // Leave relay1 off
		} else relay1(1); // Turn relay1 on
		usleep(500000);

		// Relay 2 Humidifier
		relay2(0); // Turn relay2 off
		usleep(500000);

		// Relay 3 Circulatory Fan
		relay3(0); // Turn relay3 off
		usleep(500000);

		// Relay 4 Heat
		relay4(0); // Turn relay4 off
	}
	else if ( tempState == 1 && (humState == 2 || humState == 3) )
	{
		// Relay 1 HEPA
		relay1(0); // Turn relay1 off
		usleep(500000);

		// Relay 2 Humidifier
		relay2(0); // Turn relay2 off
		usleep(500000);

		// Relay 3 Circulatory Fan
		relay3(0); // Turn relay3 off
		usleep(500000);

		// Relay 4 Heater
		if (timestampL - RHeatTS - RHeatt[RHeatt[0]] < (int)(RHeato[RHeatt[0]]*wfactor)) { // If not end of on and off timer
			if (timestampL - RHeatTS < RHeatt[RHeatt[0]]) { // If not at end of on timer
				relay4(2); // Leave relay4 on
			} else {
				if ((int)(RHeato[RHeatt[0]]*wfactor) + RHeatt[RHeatt[0]] - (timestampL - RHeatTS) <= 0) relay4(1); // Turn relay4 on
				else relay4(3); // Leave relay4 off
			}
		} else relay4(1); // Turn relay4 on
	}
	else if (tempState == 2 && (humState == 2 || humState == 3))
	{
		// Relay 1 HEPA
		relay1(0); // Turn relay1 off
		usleep(500000);

		// Relay 2 Humidifier
		relay2(0); // Turn relay2 off
		usleep(500000);

		// Relay 3 Circulatory Fan
		relay3(0); // Turn relay3 off
		usleep(500000);

		// Relay 4 Heater
		relay4(0); // Turn relay4 off
	}
	else printf("Something went wrong!\n");

	if (sleept <= 0) {
		printf("\nsleept <= 0 (review for errors in code!). Setting to 60.");
		sleep( 60 );
	} else {
		printf("\nRefresh in %d seconds.\n", sleept);
		sleep( sleept );
	}

	return 0;
}

