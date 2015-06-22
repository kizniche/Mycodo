/* To compile, use
   gcc TempHumControl-0.1.c -I/usr/local/include -L/usr/local/lib -lwiringPi -o TempHumControl
   To execute, use
   TempHumControl `tail -n 1 /home/kiz/Ter/PiSensorData`
*/

#include <stdio.h>
#include <string.h>
#include <wiringPi.h>
#include <time.h>

// Relay1 Pin - wiringPi pin  is BCM_GPIO .
// Relay2 Pin - wiringPi pin  is BCM_GPIO .
// Relay3 Pin - wiringPi pin 6 is BCM_GPIO 25.
// Relay4 Pin - wiringPi pin  is BCM_GPIO .

#define RHeat     5
#define RHum      4
#define RHepa     6
#define RFan      1
#define SIZE 256

int highTemp = 88;
int offTemp = 85;
int onTemp = 60;
int offHum = 80;
int onHum = 60;

int tempState = 0;
int humState = 0;

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

int main( int argc, char *argv[] )
{
  if (!argc)
  {
    printf("Missing input argument!\n");
    return 1;
  }

  char buffer[SIZE];
  char *tzone;
  time_t timestamp;
  char* format;
  timestamp = time(NULL);
  format = "%Y-%m-%e %H:%M:%S%n";

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

  printf("Last Read:    %s-%s-%s %s:%s:%s\n", argv[1], argv[2], argv[3], argv[4], argv[5], argv[6]);

  printf("Current: %i\nLast:    %i\n", (int) timestamp, timestampL);
  
  int tdiff = timestamp - timestampL;
  printf("Seconds since last read: %i\n", tdiff);  

  printf("Temperature (%i - %i): %s ", onTemp, offTemp, argv[10]);
  CheckTemp();

  printf("Humidity    (%i - %i): %s ", onHum, offHum, argv[8]);
  CheckHum();

  ChangeRelays();

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
    printf("Heat on, Hepa fan on, Humidifier on, Circulatory fan on.\n");
    pinMode (RHeat, OUTPUT);
    digitalWrite (RHeat, 1);
    pinMode (RHepa, OUTPUT);
    digitalWrite (RHepa, 1);
    pinMode (RHum, OUTPUT);
    digitalWrite (RHum, 1);
    pinMode (RFan, OUTPUT);
    digitalWrite (RFan, 1);
  }
  else if ( (tempState == 2 && humState == 1) || (tempState == 4 && humState == 1) )
  {
    printf("Heat off, Hepa fan off, Humidifier on, Circulatory fan on.\n");
    pinMode (RHeat, OUTPUT);
    digitalWrite (RHeat, 0);
    pinMode (RHepa, OUTPUT);
    digitalWrite (RHepa, 0);
    pinMode (RHum, OUTPUT);
    digitalWrite (RHum, 1);
    pinMode (RFan, OUTPUT);
    digitalWrite (RFan, 1);
  }
  else if ( tempState == 3 && humState == 1 )
  {
    printf("Heat off, Hepa fan on, Humidifier on, Circulatory fan on.\n");
    pinMode (RHeat, OUTPUT);
    digitalWrite (RHeat, 0);
    pinMode (RHepa, OUTPUT);
    digitalWrite (RHepa, 1);
    pinMode (RHum, OUTPUT);
    digitalWrite (RHum, 1);
    pinMode (RFan, OUTPUT);
    digitalWrite (RFan, 1);
  }
  else if ( (tempState == 1 && (humState == 2 || humState == 3) ) )
  {
    printf("Heat on, Hepa fan on, Humidifier off, Circulatory fan on.\n");
    pinMode (RHeat, OUTPUT);
    digitalWrite (RHeat, 1);
    pinMode (RHepa, OUTPUT);
    digitalWrite (RHepa, 1);
    pinMode (RHum, OUTPUT);
    digitalWrite (RHum, 0);
    pinMode (RFan, OUTPUT);
    digitalWrite (RFan, 1);
  }
  else if ( ((tempState == 2 || tempState == 4) && (humState == 2 || humState == 4)) )
  {
    printf("All Relays off.\n");
    pinMode (RHeat, OUTPUT);
    digitalWrite (RHeat, 0);
    pinMode (RHepa, OUTPUT);
    digitalWrite (RHepa, 0);
    pinMode (RHum, OUTPUT);
    digitalWrite (RHum, 0);
    pinMode (RFan, OUTPUT);
    digitalWrite (RFan, 0);
  }
  else printf("Something went wrong!\n");
  return 0; 
}
