
// QUAD ENCODER:
#define encoder0PinA 12 //2
#define encoder0PinB 13 //3
# define encoder0InterruptA 2
# define encoder0InterruptB 3

volatile unsigned int encoder0Pos = 0;

void setup() {

  pinMode(encoder0PinA, INPUT); 
  digitalWrite(encoder0PinA, LOW); // pull up resistors  
  pinMode(encoder0PinB, INPUT); 
  digitalWrite(encoder0PinB, LOW); // pull up resistors  
// encoder pin on interrupt 0 (pin 2)

  attachInterrupt(encoder0InterruptA, doEncoderA, CHANGE);
// encoder pin on interrupt 1 (pin 3)

  //attachInterrupt(encoder0InterruptB, doEncoderB, CHANGE);  
  Serial.begin (9600);
}

void loop(){ //Do stuff here 

  //Serial.println("no turns detected");

}

void doEncoderA(){

  // look for a low-to-high on channel A
  if (digitalRead(encoder0PinA) == HIGH) { 
    // check channel B to see which way encoder is turning
    if (digitalRead(encoder0PinB) == LOW) {  
      encoder0Pos = encoder0Pos + 1;         // CW
    } 
    else {
      encoder0Pos = encoder0Pos - 1;         // CCW
    }
  }
  else   // must be a high-to-low edge on channel A                                       
  { 
    // check channel B to see which way encoder is turning  
    if (digitalRead(encoder0PinB) == HIGH) {   
      encoder0Pos = encoder0Pos + 1;          // CW
    } 
    else {
      encoder0Pos = encoder0Pos - 1;          // CCW
    }
  }
  Serial.println (encoder0Pos, DEC);              
  // use for debugging - remember to comment out
}

void doEncoderB(){

  // look for a low-to-high on channel B
  if (digitalRead(encoder0PinB) == HIGH) {   
   // check channel A to see which way encoder is turning
    if (digitalRead(encoder0PinA) == HIGH) {  
      encoder0Pos = encoder0Pos + 1;         // CW
    } 
    else {
      encoder0Pos = encoder0Pos - 1;         // CCW
    }
  }
  // Look for a high-to-low on channel B
  else { 
    // check channel B to see which way encoder is turning  
    if (digitalRead(encoder0PinA) == LOW) {   
      encoder0Pos = encoder0Pos + 1;          // CW
    } 
    else {
      encoder0Pos = encoder0Pos - 1;          // CCW
    }
  }
}


