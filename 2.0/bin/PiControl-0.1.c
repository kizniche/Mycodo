/* To compile, use
   gcc TempHumControl-0.1.c -I/usr/local/include -L/usr/local/lib -lwiringPi -o TempHumControl
   To execute, use
   TempHumControl `tail -n 1 /home/kiz/Ter/PiSensorData`
*/

#include <stdio.h>
#include <string.h>
#include <wiringPi.h>

// Relay1 Pin - wiringPi pin  is BCM_GPIO .
// Relay2 Pin - wiringPi pin  is BCM_GPIO .
// Relay3 Pin - wiringPi pin 6 is BCM_GPIO 25.
// Relay4 Pin - wiringPi pin  is BCM_GPIO .

#define R1     
#define R2     
#define R3     6
#define R4     

/* int main(void)
{
  printf ("Raspberry Pi blink\n") ;

  if (wiringPiSetup() == -1)
    return 1;

  pinMode (R3, OUTPUT);

  for (;;)
  {
    digitalWrite (R3, 1);     // On
    delay (500);              // mS
    digitalWrite (R3, 0);     // Off
    delay (500);
  }
  return 0;
} */

int main( int argc, char *argv[] )
{
  if (!argc)
  {
    printf("Missing input argument!\n");
    return 1;
  }

  printf("Time: %s\nHumidity: %s\nTemperature: %s\n", argv[1], argv[2], argv[4]);


  return 0;
}

/*int chktemp(void)
{
  
}

int chkhum(void)
{
  
}*/
