// Flip motor controller
//
// Protocol (line commands — send text then newline):
//   p   = flip 180 degrees (sets new home)
//   h   = return to home
//   cw  = jog clockwise
//   ccw = jog counterclockwise
//   s   = stop whatever is moving
//   ?   = print the human-readable menu
//
// Every command answers with exactly ONE line so the backend can read an ack:
//   OK <cmd>            accepted
//   ERR <reason>        rejected
//   DONE <cmd> <pos>    a p/h move finished (sent later, when motion ends)
//
// Nothing blocks. p and h used to spin inside a while() until the move
// finished, which left the board deaf for ~20s: 's' could not interrupt and
// incoming bytes overflowed the 64-byte serial buffer, corrupting later
// commands. Motion now advances one step per loop() instead.

#include <AccelStepper.h>

const int flipStepPin = 3;
const int flipDirPin = 4;
const int flipEnPin = 2;

#define motorInterfaceType 1
AccelStepper stepper(motorInterfaceType, flipStepPin, flipDirPin);

const long stepsFor180 = 36000;
const int jogSpeed = 1000;

bool flipped = false;
long homePosition = 0;

enum State { IDLE, JOGGING_CW, JOGGING_CCW, MOVING };
State state = IDLE;
char movingCmd = ' ';  // which command owns the current MOVING run

// Fixed buffer instead of String: no heap churn, and a garbage burst cannot
// grow it without bound.
const uint8_t BUF_MAX = 16;
char inputBuffer[BUF_MAX + 1];
uint8_t inputLen = 0;
bool overflowed = false;

void printFlipMenu() {
  Serial.println("Commands:");
  Serial.println("  p   = flip 180 degrees (sets new home)");
  Serial.println("  h   = return to home");
  Serial.println("  cw  = jog clockwise");
  Serial.println("  ccw = jog counterclockwise");
  Serial.println("  s   = stop");
  Serial.print("Current home: ");
  Serial.println(homePosition);
}

// Motion commands are refused while anything is already running, so a second
// 'p' cannot start a second flip and a jog cannot fight a move in progress.
// 's' and '?' are always accepted, and 'h' may also interrupt a jog.
bool busy() {
  return state != IDLE;
}

void handleFlipCommand(const char *cmd) {
  bool isMotion = strcmp(cmd, "p") == 0 || strcmp(cmd, "h") == 0 ||
                  strcmp(cmd, "cw") == 0 || strcmp(cmd, "ccw") == 0;

  // Home is the way out of a jog: it cancels the jog and drives back to the
  // stored home, so you do not have to press stop first.
  bool jogging = state == JOGGING_CW || state == JOGGING_CCW;
  bool homeDuringJog = strcmp(cmd, "h") == 0 && jogging;

  if (isMotion && busy() && !homeDuringJog) {
    Serial.print("ERR busy ");
    if (state == MOVING) {
      Serial.println(movingCmd == 'p' ? "flipping" : "homing");
    } else {
      Serial.println(state == JOGGING_CW ? "jogging cw" : "jogging ccw");
    }
    return;
  }

  if (strcmp(cmd, "p") == 0) {
    flipped = !flipped;
    stepper.moveTo(flipped ? stepsFor180 : 0);
    state = MOVING;
    movingCmd = 'p';
    Serial.println("OK p");

  } else if (strcmp(cmd, "h") == 0) {
    stepper.moveTo(homePosition);
    state = MOVING;
    movingCmd = 'h';
    Serial.println("OK h");

  } else if (strcmp(cmd, "cw") == 0) {
    state = JOGGING_CW;
    stepper.setSpeed(jogSpeed);
    Serial.println("OK cw");

  } else if (strcmp(cmd, "ccw") == 0) {
    state = JOGGING_CCW;
    stepper.setSpeed(-jogSpeed);
    Serial.println("OK ccw");

  } else if (strcmp(cmd, "s") == 0) {
    // A cancelled flip never reached the far side, so undo the toggle or the
    // next 'p' would drive the wrong way.
    if (state == MOVING && movingCmd == 'p') {
      flipped = !flipped;
    }

    // Cancel a targeted move by retargeting the current position, so the
    // library stops asking for more steps.
    stepper.moveTo(stepper.currentPosition());
    state = IDLE;
    movingCmd = ' ';
    Serial.print("OK s ");
    Serial.println(stepper.currentPosition());

  } else if (strcmp(cmd, "?") == 0) {
    printFlipMenu();

  } else {
    Serial.println("ERR unknown");
  }
}

void readSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (overflowed) {
        Serial.println("ERR overflow");
      } else if (inputLen > 0) {
        inputBuffer[inputLen] = '\0';
        handleFlipCommand(inputBuffer);
      }
      inputLen = 0;
      overflowed = false;

    } else if (inputLen < BUF_MAX) {
      inputBuffer[inputLen++] = c;

    } else {
      overflowed = true;  // drop the rest of this line, report at newline
    }
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
  // Serial first: 's' must be able to interrupt a flip already in progress.
  readSerial();

  if (state == JOGGING_CW || state == JOGGING_CCW) {
    stepper.runSpeed();

  } else if (state == MOVING) {
    stepper.run();

    if (stepper.distanceToGo() == 0) {
      if (movingCmd == 'p') {
        homePosition = stepper.currentPosition();
      }
      Serial.print("DONE ");
      Serial.print(movingCmd);
      Serial.print(' ');
      Serial.println(stepper.currentPosition());
      state = IDLE;
      movingCmd = ' ';
    }
  }
}
