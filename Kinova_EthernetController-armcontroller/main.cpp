#include <iostream>
#include <conio.h>    // _kbhit(), _getch() for detecting keys
#include <fstream>
#include <windows.h>
#include "robot.h"
#include "movements.h"
#include <map>
#include <functional>
#include <string>

// =============================================================
// main.cpp : Shervin Naini
// =============================================================
// PURPOSE:
//   Entry point for the KinovaController program.
//   Initializes the robot ONCE at startup, then runs a
//   permanent command loop reading instructions from Python
//   via stdin pipe, executing the corresponding movement,
//   and returning "done" to Python via stdout.
//
//   The DLL is loaded and the Ethernet connection is established
//   ONCE — not reinitalized on every command. This keeps
//   latency low (~10-50ms per command vs ~1300ms per subprocess).
//
// DEPENDENCIES:
//   - robot.h      : InitializeRobot(), CleanupRobot()
//   - movements.h  : MoveHome() and all directional movements
//   - iostream     : cin, cout
//   - string       : getline, string
//
// COMMUNICATION PROTOCOL (Python ↔ C++ via pipe):
//   Python sends  → "home", "right", "left", "up", "down",
//                   "forward", "backward", "stop", "quit"
//   C++ responds  → "READY" once initialized
//                 → "done"  after each command completes
//                 → "error" if command is unrecognized
//
// USAGE:
//   Started ONCE by Python backend via subprocess.Popen()
//   Python writes commands to stdin, reads responses from stdout
//
// EXAMPLE (Python side):
//   process = subprocess.Popen(["KinovaController.exe"],
//                               stdin=subprocess.PIPE,
//                               stdout=subprocess.PIPE,
//                               text=True)
//   process.stdout.readline()        # waits for "READY"
//   process.stdin.write("home\n")    # sends command
//   process.stdin.flush()
//   process.stdout.readline()        # waits for "done"
//
// LIFECYCLE:
//   1. InitializeRobot()  — load DLL, connect, find robot
//   2. Print "READY"      — signal Python we are ready
//   3. Loop forever       — read command → execute → print "done"
//   4. CleanupRobot()     — disconnect and unload DLL on "quit"
// =============================================================


#ifndef UNICODE
#define UNICODE
#endif

using namespace std;



//std::map<std::string, std::pair<char, std::function<void()>>> directionMap = {
//			{"right", {'d', MoveRight}},
//			{"left",  {'a', MoveLeft}},
//			{"up",    {'w', MoveUp}},
//			{"down",  {'s', MoveDown}},
//};
//
//void commandLoop(char triggerKey, std::function<void()> MoveFunc) {
//	cout << "Press '" << triggerKey << "' to move, press 'o' to exit command center" << endl;
//	while (true) {
//		if (_kbhit()) {
//			char key = _getch();
//			if (key == triggerKey) {
//				MoveFunc();
//			}
//			else if (key == 'o') {
//				cout << "Exiting command zone" << endl;
//				break;
//			}
//		}
//	}
//	};


/*
## Daemon is a program that runs in the background without a person actively typing into it 
## or watching it, it just sits there doing its job and responding when something asks it to
## "helpful spirit" 
##
##
##*/


int run_daemon_mode() {
	int result = InitializeRobot();
	Sleep(5000);
	if (!result) {
		cout << "ERROR" << endl;
		return 1;
	}
	cout << "READY" << endl;

	string line;
	while (getline(cin, line)) {
		if (line == "quit") {
			break;
		}
		else if (line == "coordinates") {
			myCurrentLocation();
			cout << "done" << endl;
		}
		//else if (line == "home") {
		//	MovingtoHome();
		//	cout << "done" << endl;
		//}
		else if (line == "left") {
			MoveLeft();
			cout << "done" << endl;
		}
		else if (line == "right") {
			MoveRight();
			cout << "done" << endl;
		}
		else if (line == "up") {
			MoveUp();
			cout << "done" << endl;
		}
		else if (line == "down") {
			MoveDown();
			cout << "done" << endl;
		}
		else if (line == "home") {
			Shervins_Home();
			cout << "done" << endl;
		}
		else if (line == "in") {
			MoveIn();
			cout << "done" << endl;
		}
		else if (line == "out") {
			MoveOut();
			cout << "done" << endl;
		}
		else if (line == "retract") {
			Shervins_Rest();
			cout << "done" << endl;
		}
		else {
			cout << "error" << endl;
		}
	}

	CleanupRobot();
	return 0;
}


int main(int argc, char* argv[]) {
	if (argc > 1 && string(argv[1]) == "--daemon") {
		return run_daemon_mode();
	}

	// Console test — run the exe with no --daemon, in a real terminal.
	if (!InitializeRobot()) {
		cout << "Initialization failed" << endl;
		return 1;
	}

	cout << "u = hold up,  d = hold down,  s = stop,  q = quit" << endl;

	while (true) {
		if (!_kbhit()) continue;
		char key = _getch();

		if (key == 'q') break;

		if (key == 'u' || key == 'd') {
			while (true) {
				if (key == 'u') MoveUp();
				else MoveDown();
				cout << "done" << endl;

				if (_kbhit()) {
					char stop = _getch();
					if (stop == 's') break;  // was checking key, not stop
				}
			}
		}
	}

	CleanupRobot();
	return 0;
}