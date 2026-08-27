// Flip motor controller
//
// Protocol (line commands — send text then newline):
//   p   = flip 180 degrees (sets new home)
//   h   = return to home
//   cw  = jog clockwise
//   ccw = jog counterclockwise
//   s   = stop flip jog

#include <AccelStepper.h>

const int flipStepPin = 3;
const int flipDirPin = 4;
const int flipEnPin = 2;

#define motorInterfaceType 1
AccelStepper stepper(motorInterfaceType, flipStepPin, flipDirPin);

const long stepsFor180 = 36000;
bool flipped = false;
long homePosition = 0;

enum State { IDLE, JOGGING_CW, JOGGING_CCW };
State state = IDLE;

String inputBuffer = "";

void printFlipMenu() {
  Serial.println("Commands:");
  Serial.println("  p   = flip 180 degrees (sets new home)");
  Serial.println("  h   = return to home");
  Serial.println("  cw  = jog clockwise");
  Serial.println("  ccw = jog counterclockwise");
  Serial.println("  s   = stop flip jog");
  Serial.print("Current home: ");
  Serial.println(homePosition);
}

void handleFlipCommand(String cmd) {
  cmd.trim();

  if (cmd == "p") {
    state = IDLE;
    flipped = !flipped;
    long target = flipped ? stepsFor180 : 0;
    stepper.moveTo(target);
    while (stepper.distanceToGo() != 0) stepper.run();
    homePosition = stepper.currentPosition();
    Serial.print("Flipped! New home set to: ");
    Serial.println(homePosition);

  } else if (cmd == "h") {
    state = IDLE;
    stepper.moveTo(homePosition);
    while (stepper.distanceToGo() != 0) stepper.run();
    Serial.print("Returned to home: ");
    Serial.println(homePosition);

  } else if (cmd == "cw") {
    state = JOGGING_CW;
    stepper.setSpeed(1000);
    Serial.println("Jogging CW — type 's' to stop");

  } else if (cmd == "ccw") {
    state = JOGGING_CCW;
    stepper.setSpeed(-1000);
    Serial.println("Jogging CCW — type 's' to stop");

  } else if (cmd == "s") {
    state = IDLE;
    stepper.stop();
    Serial.print("Flip stopped at position: ");
    Serial.println(stepper.currentPosition());
  }
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(flipEnPin, OUTPUT);
  digitalWrite(flipEnPin, LOW);

  stepper.setMaxSpeed(2000);
  stepper.setAcceleration(2000);
  stepper.setCurrentPosition(0);

  printFlipMenu();
  Serial.println("PROMPT_FLIP");  // waiting for a line command
}

void loop() {
  if (state == JOGGING_CW || state == JOGGING_CCW) {
    stepper.runSpeed();
  }

  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        handleFlipCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}
