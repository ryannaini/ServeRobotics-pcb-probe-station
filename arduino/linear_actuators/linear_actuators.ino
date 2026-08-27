// Linear actuator controller (top = 3, bottom = 4)
//
// Protocol (one char at a time, no newline required):
//   3 or 4  -> enter actuator, prints ACTUATOR_READY then PROMPT_SCALE
//   1 or 2  -> slow / fast (asked once, can be changed any time)
//   f       -> move forward until 's'   (enable LOW while moving)
//   b       -> move backward until 's'  (enable LOW while moving)
//   t       -> single step forward
//   s       -> stop move, enable back HIGH
//   o       -> exit actuator, back to PROMPT_TOP

#define STEP_PIN1   9
#define DIR_PIN1    10
#define ENABLE_PIN1 8

#define STEP_PIN2   5
#define DIR_PIN2    7
#define ENABLE_PIN2 6

// Red = 1B, Blue 1A, Black = 2A, Green = 2B

int STEP_PIN, DIR_PIN, ENABLE_PIN;
int scale = 1;

// Wait for one command char; ignore CR/LF noise from Serial Monitor / hosts.
char readCommandChar() {
  while (true) {
    while (Serial.available() == 0) {
      // idle until a byte arrives
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

// Runs until 's' arrives; enable is released by the caller.
void moveUntilStop(bool forward) {
  digitalWrite(DIR_PIN, forward ? HIGH : LOW);
  while (true) {
    stepActuator(scale);
    if (Serial.available() > 0) {
      char stop = Serial.read();
      if (stop == '\r' || stop == '\n') continue;
      if (tolower(stop) == 's') {
        Serial.println("ACTUATOR_STOPPED");
        return;
      }
    }
  }
}

void runActuator(int value) {
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
  digitalWrite(ENABLE_PIN, HIGH);  // disabled until a move starts

  Serial.print("ACTUATOR_READY ");
  Serial.println(value);

  // Speed is asked once here; f/b/t afterwards reuse it.
  bool haveScale = false;
  while (!haveScale) {
    Serial.println("PROMPT_SCALE");
    char val = readCommandChar();

    if (tolower(val) == 'o') {
      Serial.println("ACTUATOR_EXIT");
      digitalWrite(ENABLE_PIN, HIGH);
      return;
    }

    scale = val - '0';
    if (scale == 1 || scale == 2) {
      haveScale = true;
    } else {
      Serial.println("ERR_SCALE");
    }
  }

  while (true) {
    Serial.println("PROMPT_DIR");
    char input = tolower(readCommandChar());

    if (input == 'f' || input == 'b') {
      Serial.println(input == 'f' ? "MOVING_FWD" : "MOVING_BWD");
      digitalWrite(ENABLE_PIN, LOW);   // enable only while moving
      moveUntilStop(input == 'f');
      digitalWrite(ENABLE_PIN, HIGH);  // released on stop

    } else if (input == 't') {
      Serial.println("STEP_ONCE");
      digitalWrite(ENABLE_PIN, LOW);
      digitalWrite(DIR_PIN, HIGH);
      stepActuator(scale);
      digitalWrite(ENABLE_PIN, HIGH);

    } else if (input == '1' || input == '2') {
      scale = input - '0';
      Serial.print("SCALE_SET ");
      Serial.println(scale);

    } else if (input == 's') {
      // stop with nothing moving — make sure driver is released
      digitalWrite(ENABLE_PIN, HIGH);
      Serial.println("ACTUATOR_STOPPED");

    } else if (input == 'o') {
      Serial.println("ACTUATOR_EXIT");
      digitalWrite(ENABLE_PIN, HIGH);
      return;

    } else {
      Serial.println("ERR_DIR");
    }
  }
}

void printActuatorMenu() {
  Serial.println("Commands:");
  Serial.println("  3   = select top actuator");
  Serial.println("  4   = select bottom actuator");
  Serial.println("  then 1 (slow) or 2 (fast)");
  Serial.println("  then f (forward), b (backward), t (step once)");
  Serial.println("  1/2 = change speed any time");
  Serial.println("  s   = stop move");
  Serial.println("  o   = exit actuator");
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  pinMode(ENABLE_PIN1, OUTPUT);
  pinMode(ENABLE_PIN2, OUTPUT);
  digitalWrite(ENABLE_PIN1, HIGH);
  digitalWrite(ENABLE_PIN2, HIGH);

  printActuatorMenu();
  Serial.println("PROMPT_TOP");  // waiting for 3 or 4
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '3' || c == '4') {
      runActuator(c - '0');
      printActuatorMenu();
      Serial.println("PROMPT_TOP");
    }
    // any other byte at top level is ignored (CR/LF, stray chars)
  }
}
