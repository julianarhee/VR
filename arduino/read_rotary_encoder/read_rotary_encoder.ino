
/* Rotary encoder read example */

// Port pin names: ---------------------------------------------------
// For pins 14, 15, ENC_PORT is PINB
// For pins 0, 1, ENC_PORT is PIND
// But, just use pins 8,9, and set ENC_PORT to PINB

#define ENC_A 8// 2 //14
#define ENC_B 9 //3 //15
#define ENC_PORT PINB // PIND //PINC

// ----------------------------------------------------------------------------

void setup()
{
  /* Setup encoder pins as inputs */
  pinMode(ENC_A, INPUT);    // set encoder pin A as input to read from it
  digitalWrite(ENC_A, HIGH); // turn on pull-up resistor in pin so won't dangle when switch open
  pinMode(ENC_B, INPUT);
  digitalWrite(ENC_B, HIGH);
  //Serial.begin (115200);
  Serial.begin (9600);
  Serial.println("Start");       // serial port is working if "Start" in terminal
}
 
void loop()
{
 static uint8_t counter = 0;      //this variable will be changed by encoder input
 //static uint16_t counter = 0;      //this variable will be changed by encoder input
 int8_t tmpdata;
 //uint16_t tmpdata;
 /**/
  tmpdata = read_encoder();
  if( tmpdata ) {
    Serial.print("Counter value: ");
    Serial.println(counter, DEC);
    counter += tmpdata;
  }
}
 
/* returns change in encoder state (-1,0,1) */
int8_t read_encoder()
//uint16_t read_encoder()
{
  static int8_t enc_states[] = {0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
  static uint8_t old_AB = 0;   // static, value retained between function calls
  /**/
  old_AB <<= 2;                   // remember previous state (shift LEFT two times, set last 2 bits to 0)
  old_AB |= ( ENC_PORT & 0x03 );  // add current state (use & to get new pin vals into lower two bits)
  /*  */
  return ( enc_states[( old_AB & 0x0f )]);
}
