/* To compile, use
   gcc PiControl-0.1.c -I/usr/local/include -L/usr/local/lib -lwiringPi -o PiControl
   To execute, use
   sudo PiControl `sudo /var/www/bin/PiSensordata.py -d`
*/

#include <stdio.h>
#include <string.h>
#include <wiringPi.h>
#include <time.h>

// Relay1 HEPA Pin - wiringPi pin 4 is BCM_GPIO 23, GPIO4
// Relay2 HUMI Pin - wiringPi pin 3 is BCM_GPIO 22, GPIO3
// Relay3 CFAN Pin - wiringPi pin 1 is BCM_GPIO 18, GPIO1
// Relay4 HEAT Pin - wiringPi pin 0 is BCM_GPIO 17, GPIO0

#define RHepa 4
#define RHum  3
#define RFan  1
#define RHeat 0
#define SIZE 256

int year;
int month;
int day;
int hour;
int min;
int sec;
int timestampL;
time_t timestamp;
int hum;
int temp;

char line[256];
int linenum=0;
char sonTemp[256], soffTemp[256], shighTemp[256], sonHum[256], soffHum[256], sweboverride[256];

int highTemp = 85;
int offTemp = 81;
int onTemp = 75;
int offHum = 80;
int onHum = 60;
int weboverride = 0;

int tempState = 0;
int humState = 0;

int main( int argc, char *argv[] )
{
  if (!argc)
  {
    printf("Missing input argument!\n");
    return 1;
  }

  FILE * pFile;
  pFile = fopen ("/var/www/graph/PiConfig" , "r");
  while(fgets(line, 256, pFile) != NULL)
  {
    linenum++;
    if(line[0] == '#') continue;

    if(sscanf(line, "%s %s %s %s %s %s", sonTemp, soffTemp, shighTemp, sonHum, soffHum, sweboverride) != 6)
    {
      fprintf(stderr, "Config file syntax error\n", linenum);
      continue;
    }
    printf("onTemp offTemp highTemp onHum offHum override\n%s %s %s %s %s %s\n", sonTemp, soffTemp, shighTemp, sonHum, soffHum, sweboverride);
  }

  onTemp = atoi(sonTemp);
  offTemp = atoi(soffTemp);
  highTemp = atoi(shighTemp);
  onHum = atoi(sonHum);
  offHum = atoi(soffHum);
  weboverride = atoi(sweboverride);

  if (wiringPiSetup() == -1)
  {
    printf("wiringPiSetup returned -1!\n");
    return 1;
  }

  pinMode (RHeat, OUTPUT);
  pinMode (RHum, OUTPUT);
  pinMode (RHepa, OUTPUT);
  pinMode (RFan, OUTPUT);

  char buffer[SIZE];
  char *tzone;
  time_t timestamp;
  char* format;
  timestamp = time(NULL);
  format = "%Y-%m-%e %H:%M:%S";

  year = atoi(argv[1]);
  month  = atoi(argv[2]);
  day  = atoi(argv[3]);
  hour  = atoi(argv[4]);
  min  = atoi(argv[5]);
  sec  = atoi(argv[6]);
  timestampL = atoi(argv[7]);
  hum = atoi(argv[8]);
  temp = atoi(argv[10]);
  
  printf("Current Time: ");

  tzone="TZ=EST";
  putenv(tzone);
  strftime(buffer, SIZE, format, localtime(&timestamp));
  fputs(buffer, stdout);

  printf(" %i\n", (int) timestamp);

  printf("Last Read:    %s-%s-%s %s:%s:%s %i\n", argv[1], argv[2], argv[3], argv[4], argv[5], argv[6], timestampL);

  int tdiff = timestamp - timestampL;
  printf("Seconds since last read: %i\n", tdiff);  

  printf("Temperature (%i - %i): %s ", onTemp, offTemp, argv[10]);
  CheckTemp();

  printf("Humidity    (%i - %i): %s ", onHum, offHum, argv[8]);
  CheckHum();

  if (!weboverride) { ChangeRelays(); }
  else { printf("WebOverride activated - No relay change!\n"); }

  return 0;
}


int CheckTemp (void)
{
  if ( temp < onTemp )
  {
    tempState = 1;
    printf("Below threshhold.\n");
  }
  else if ( temp >= offTemp && temp <= highTemp )
  {
    tempState = 2;
    printf("At or above threshhold.\n");
  }
  else if ( temp >= highTemp )
  {
    tempState = 3;
    printf("Becoming critically high.\n");
  }
  else
  {
    tempState = 4;
    printf("In range.\n");
  }
  return 0;
}


int CheckHum (void)
{
  if ( hum < onHum )
  {
    humState = 1;
    printf("Below threshhold.\n");
  }
  else if ( hum >= offHum )
  {
    humState = 2;
    printf("At or above threshhold.\n");
  }
  else
  {
    humState = 3;
    printf("In range.\n");
  }
  return 0;
}

int ChangeRelays (void)
{
//tempState 1=below 2=above 3=too high 4=in range
//humState  1=below 2=above 3=in range
  if ( tempState == 1 && humState == 1 )
  {
    printf("Heat on, Hepa fan off, Humidifier on, Circulatory fan on.\n");
    digitalWrite (RHeat, 1);
    digitalWrite (RHepa, 0);
    digitalWrite (RHum, 1);
    digitalWrite (RFan, 1);
    sleep(10);
    printf("Heat off");
    digitalWrite (RHeat, 0);
  }
  else if ( (tempState == 2 && humState == 1) || (tempState == 4 && humState == 1) )
  {
    printf("Heat off, Hepa fan off, Humidifier on, Circulatory fan on.\n");
    digitalWrite (RHeat, 0);
    digitalWrite (RHepa, 0);
    digitalWrite (RHum, 1);
    digitalWrite (RFan, 1);
  }
  else if ( tempState == 3 && humState == 1 )
  {
    printf("Heat off, Hepa fan on, Humidifier on, Circulatory fan on.\n");
    digitalWrite (RHeat, 0);
    digitalWrite (RHepa, 1);
    digitalWrite (RHum, 1);
    digitalWrite (RFan, 1);
  }
  else if ( (tempState == 1 && (humState == 2 || humState == 3) ) )
  {
    printf("Heat on, Hepa fan off, Humidifier off, Circulatory fan on.\n");
    digitalWrite (RHeat, 1);
    digitalWrite (RHepa, 0);
    digitalWrite (RHum, 0);
    digitalWrite (RFan, 1);
    sleep(10);
    printf("Heat off");
    digitalWrite (RHeat, 0);
  }
  else if ( ((tempState == 2 || tempState == 4) && (humState == 2 || humState == 4)) )
  {
    printf("All Relays off.\n");
    digitalWrite (RHeat, 0);
    digitalWrite (RHepa, 0);
    digitalWrite (RHum, 0);
    digitalWrite (RFan, 0);
  }
  else printf("Something went wrong!\n");
  return 0; 
}
