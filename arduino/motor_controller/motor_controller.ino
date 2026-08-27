#include <AccelStepper.h>

// --- Linear actuators (top = 3, bottom = 4) ---
#define STEP_PIN1   9
#define DIR_PIN1    10
#define ENABLE_PIN1 7

#define STEP_PIN2   4
#define DIR_PIN2    5
#define ENABLE_PIN2 6

// Red = 1B, Blue 1A, Black = 2A, Green = 2B
// NOTE: STEP_PIN2 (4) shares the same pin as flipDirPin (4) — bottom actuator
// and flip direction cannot be driven independently on this wiring.

int STEP_PIN, DIR_PIN, ENABLE_PIN;
int scale = 1;

// --- Flip motor ---
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

// Wait for one command char; ignore CR/LF noise from Serial Monitor / hosts.
char readCommandChar() {
  while (true) {
    while (Serial.available() == 0) {
      // keep flip jog alive if we ever share this wait (normally idle here)
    }
    char c = Serial.read();
    if (c == '\r' || c == '\n') continue;
    return c;
  }
}

void stepActuator(int &scaleVal) {
  int RELAY_DELAY = 0;
  if (scaleVal == 1) {
    RELAY_DELAY = 800;
  } else if (scaleVal == 2) {
    RELAY_DELAY = 340;
  }

  digitalWrite(STEP_PIN, HIGH);
  delayMicroseconds(RELAY_DELAY);
  digitalWrite(STEP_PIN, LOW);
  delayMicroseconds(RELAY_DELAY);
}

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

void runActuator(int value) {
  state = IDLE;
  stepper.stop();

  if (value == 3) {
    STEP_PIN   = STEP_PIN1;
    DIR_PIN    = DIR_PIN1;
    ENABLE_PIN = ENABLE_PIN1;
  } else if (value == 4) {
    STEP_PIN   = STEP_PIN2;
    DIR_PIN    = DIR_PIN2;
    ENABLE_PIN = ENABLE_PIN2;
  } else {
    return;
  }

  pinMode(STEP_PIN,   OUTPUT);
  pinMode(DIR_PIN,    OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH);  // disabled until speed chosen

  Serial.print("ACTUATOR_READY ");
  Serial.println(value);

  while (true) {
    // Marker strings below are what Python waits for — keep them stable.
    Serial.println("PROMPT_SCALE");

    char val = readCommandChar();

    if (tolower(val) == 'o') {
      Serial.println("ACTUATOR_EXIT");
      digitalWrite(ENABLE_PIN, HIGH);
      break;
    }

    scale = val - '0';
    if (scale != 1 && scale != 2) {
      Serial.println("ERR_SCALE");
      continue;  // stay disabled (never pulled enable for bad input)
    }

    // Enable only once we have a valid speed; Python should send direction next.
    digitalWrite(ENABLE_PIN, LOW);
    Serial.println("PROMPT_DIR");

    char input = tolower(readCommandChar());

    if (input == 'f') {
      Serial.println("MOVING_FWD");
      digitalWrite(DIR_PIN, HIGH);
      while (true) {
        stepActuator(scale);
        if (Serial.available() > 0) {
          char stop = Serial.read();
          if (stop == '\r' || stop == '\n') continue;
          if (tolower(stop) == 's') {
            Serial.println("ACTUATOR_STOPPED");
            break;
          }
        }
      }
    } else if (input == 'b') {
      Serial.println("MOVING_BWD");
      digitalWrite(DIR_PIN, LOW);
      while (true) {
        stepActuator(scale);
        if (Serial.available() > 0) {
          char stop = Serial.read();
          if (stop == '\r' || stop == '\n') continue;
          if (tolower(stop) == 's') {
            Serial.println("ACTUATOR_STOPPED");
            break;
          }
        }
      }
    } else if (input == 't') {
      Serial.println("STEP_ONCE");
      digitalWrite(DIR_PIN, HIGH);
      stepActuator(scale);
    } else if (input == 'o') {
      // allow exit even at direction prompt
      Serial.println("ACTUATOR_EXIT");
      digitalWrite(ENABLE_PIN, HIGH);
      break;
    } else {
      Serial.println("ERR_DIR");
    }

    digitalWrite(ENABLE_PIN, HIGH);  // disable between moves
  }
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(ENABLE_PIN1, OUTPUT);
  pinMode(ENABLE_PIN2, OUTPUT);
  digitalWrite(ENABLE_PIN1, HIGH);
  digitalWrite(ENABLE_PIN2, HIGH);

  pinMode(flipEnPin, OUTPUT);
  digitalWrite(flipEnPin, LOW);

  stepper.setMaxSpeed(2000);
  stepper.setAcceleration(2000);
  stepper.setCurrentPosition(0);

  printFlipMenu();
  Serial.println("PROMPT_TOP");  // waiting for 3/4 or flip line-commands
}

void loop() {
  if (state == JOGGING_CW || state == JOGGING_CCW) {
    stepper.runSpeed();
  }

  while (Serial.available() > 0) {
    char c = Serial.read();

    // Actuator select always wins and clears any polluted flip buffer.
    // (Previously, a stray 'o'/'s' in inputBuffer blocked 3/4 forever.)
    if (c == '3' || c == '4') {
      inputBuffer = "";
      int VAL = c - '0';
      runActuator(VAL);
      printFlipMenu();
      Serial.println("PROMPT_TOP");
      continue;
    }

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
