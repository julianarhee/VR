//include "Arduino.h"
#include <digitalWriteFast.h>  // library for high performance reads and writes by jrraines
// see http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1267553811/0
// and http://code.google.com/p/digitalwritefast/

// It turns out that the regular digitalRead() calls are too slow and bring the arduino down when
// I use them in the interrupt routines while the motor runs at full speed creating more than
// 40000 encoder ticks per second per motor.

// Quadrature
//encoder
#define c_EncoderInterrupt 0
#define d_EncoderInterrupt 1

#define c_EncoderPinA 2
#define c_EncoderPinB 3

#define EncoderIsReversed
volatile bool _EncoderBSet;
//volatile long _EncoderTicks = 0;
//long copy_EncoderTicks = 0; //new variable for protected copy
volatile int _EncoderTicks = 0;
int copy_EncoderTicks = 0;


void setup()
{
  Serial.begin(115200);
  //Serial.begin(9600);
 
  
  // Quadrature encoder
  pinMode(c_EncoderPinA, INPUT); // sets pin A as input
  digitalWrite(c_EncoderPinA, HIGH); // turn on pullup resistors
  pinMode(c_EncoderPinB, INPUT); // sets pin B as input
  digitalWrite(c_EncoderPinB, HIGH); // turn on pullup resistors



  attachInterrupt(c_EncoderInterrupt, HandleMotorInterruptAfirst, RISING);
  

}

void loop()
{
  noInterrupts();
  copy_EncoderTicks = _EncoderTicks;
  interrupts();

//do whatever with the transferred variable
  
  Serial.println(copy_EncoderTicks); 

  delay(20);
}

void HandleMotorInterruptAfirst()
{
  // Test transition; since the interrupt will only fire on 'rising' we don't need to read pin A
  //_EncoderBSet = digitalReadFast(c_EncoderPinB); // read the input pin
  _EncoderBSet = digitalRead(c_EncoderPinB); // read the input pin
  

  // and adjust counter + if A leads B
#ifdef EncoderIsReversed
  _EncoderTicks -= _EncoderBSet ? -1 : +1;
#else
  _EncoderTicks += _EncoderBSet ? -1 : +1;
#endif


}
