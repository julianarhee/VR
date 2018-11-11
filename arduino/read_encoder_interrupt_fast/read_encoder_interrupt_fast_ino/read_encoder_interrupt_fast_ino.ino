#include <digitalWriteFast.h>  // library for high performance reads and writes by jrraines
 
#define c_LeftEncoderInterrupt 0
#define c_LeftEncoderPinA 2
#define c_LeftEncoderPinB 3
 
volatile bool _LeftEncoderBSet;
volatile long _LeftEncoderTicks = 0;
 
void setup()
{
  //Serial.begin(115200);
  Serial.begin(9600);
  pinMode(c_LeftEncoderPinA, INPUT);      
  digitalWrite(c_LeftEncoderPinA, HIGH); // not using external pullup/down resistors, set to HIGH 
  pinMode(c_LeftEncoderPinB, INPUT);
  digitalWrite(c_LeftEncoderPinB, HIGH);
  attachInterrupt(c_LeftEncoderInterrupt, HandleLeftMotorInterruptA, RISING);
}
 
// Interrupt service routines for the left motor's quadrature encoder
void HandleLeftMotorInterruptA()
{
  _LeftEncoderBSet = digitalReadFast2(c_LeftEncoderPinB);   // read the input pin
  _LeftEncoderTicks -= _LeftEncoderBSet ? -1 : +1;
}
 
void loop()
{
  Serial.println(_LeftEncoderTicks);
  ///Serial.print("\n");
  delay(20);
}
