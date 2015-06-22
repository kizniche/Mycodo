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
int hum;
int temp;

int main( int argc, char *argv[] )
{
  if (!argc)
  {
    printf("Missing input argument!\n");
    return 1;
  }

  year = atoi(argv[1]);
  month  = atoi(argv[2]);
  day  = atoi(argv[3]);
  hour  = atoi(argv[4]);
  min  = atoi(argv[5]);
  sec  = atoi(argv[6]);
  hum = atoi(argv[7]);
  temp = atoi(argv[9]);

  printf("Last Read: %s-%s-%s %s:%s:%s\n", argv[1], argv[2], argv[3], argv[4], argv[5], argv[6]);
  printf("Humidity (%i - %i): %s\n", onHum, offHum, argv[7]);
  CheckHum();
  printf("Temperature (%i - %i): %s\n", onTemp, offTemp, argv[9]);
  CheckTemp();

  ChangeRelays();

  return 0;
}


int CheckTemp (void)
{
  if ( temp < onTemp )
  {
    tempState = 1;
    printf("Temperature below threshhold.\n");
  }
  else if ( temp >= offTemp && temp <= highTemp )
  {
    tempState = 2;
    printf("Temperature at above threshhold.\n");
  }
  else if ( temp >= highTemp )
  {
    tempState = 3;
    printf("Temperature becoming critically high.\n");
  }
  else
  {
    tempState = 4;
    printf("Temperature in range.\n");
  }
  return 0;
}


int CheckHum (void)
{
  if ( hum < onHum )
  {
    humState = 1;
    printf("Humidity below threshhold.\n");
  }
  else if ( hum >= offHum )
  {
    humState = 2;
    printf("Temperature at or above threshhold.\n");
    pinMode (RHum, OUTPUT);
    pinMode (RFan, OUTPUT);
    digitalWrite (RHum, 0);
    digitalWrite (RFan, 0);
  }
  else
  {
    humState = 3;
    printf("Humidity in range.\n");
  }
  return 0;
}

int ChangeRelays (void)
{
 
  return 0; 
}
