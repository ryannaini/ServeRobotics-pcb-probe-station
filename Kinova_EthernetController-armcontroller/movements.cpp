// =============================================================
// movements.cpp
// 
// 
// By: Shervin Naini
// =============================================================
// PURPOSE:
//   Implements all robot movement functions declared in movements.h
//   Uses global function pointers from robot.h to send commands
//   to the Kinova Gen2 arm via the Ethernet SDK
//
// DEPENDENCIES:
//   - movements.h : function declarations
//   - robot.h     : global function pointers (MySendBasicTrajectory,
//                   MyGetCartesianCommand, MyEraseAllTrajectories); packaged by Shervin Naini
//   - KinovaTypes.h : TrajectoryPoint, CartesianPosition, CARTESIAN_POSITION
//   - windows.h   : Sleep()
//
// NOTES:
//   - CARTESIAN_POSITION sends ONE command, robot moves to target autonomously
//   - Home XYZ coordinates must be calibrated physically and hardcoded below


#include "movements.h"
#include <iostream>
#include <fstream>
#include <windows.h>

using namespace std;


// =============================================================
// MoveHome
// =============================================================
// Moves the arm to the custom PCB probing home position
// using CARTESIAN_POSITION — sent once, robot moves autonomously
// =============================================================


// Because we called extern to all the pointers, they live across all different files hence 
// We can check to see if functions are intialized or not. 


/*
 * ---------------------------------------------------------------
 * @brief       Moves the robot to the custom home position for
 *              PCB probing operations.
 *
 * @pre         InitializeRobot() must be called before this.
 *
 * @param       int; result of initalize robot 
 * 
 * @note		This MoveHome is Called after Initialize Robot which moves
 *				the robot to Kinova MoveHome() API Call then it positions
 *				the robot back for adjustments then moves it again to its
 *				final home position 
 * 
 * @return      Bool (True or False if it completed)
 * ---------------------------------------------------------------
 */

bool homePositionSet = false;


// Desired Shervin's homing place 
const float home[7] = { 180.27f, 224.26f, 178.92f, 311.53f, 3.08f, 95.81f, 255.88f }; 

const float rest[7] = { 90.27f , 224.26f, 178.92f, 311.53f, 3.08f, 95.81f, 255.88f };



/*
	@brief		This function must be called after MoveHome() as the reference position
				is dependent on being at home base 
	
	@prereq		A Global Flag must be created set to false before MoveHome() is called
				Then this function checks if that has been set to true 

	@param		Scale Factor, How much to move right (1, 5, 10)

	@return		Void 

*/

void MoveRight() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl;
		return;
	}

	

	TrajectoryPoint command;
	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;
	command.Position.CartesianPosition.X = 0.15;
	command.Position.CartesianPosition.Y = 0.0;
	command.Position.CartesianPosition.Z = 0.0;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = 0.4;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendAdvanceTrajectory)(command);
	Sleep(30);
	
}

void MoveLeft() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl; return;
	}
	
	TrajectoryPoint command;

	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;

	command.Position.CartesianPosition.X = - 0.15;
	command.Position.CartesianPosition.Y = 0.0;
	command.Position.CartesianPosition.Z = 0.0;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = - 0.4;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendAdvanceTrajectory)(command);
	Sleep(30);
}

void MoveUp() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl; return;
	}

	int mode = -1;
	int api = MyGetControlType(mode);
	cout << "GetControlType api=" << api << " mode=" << mode
		<< (mode == 0 ? " CARTESIAN" : mode == 1 ? " ANGULAR" : " OTHER")
		<< endl;

	MyEraseAllTrajectories();
	TrajectoryPoint command;

	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;

	command.Position.CartesianPosition.X = 0.0;
	command.Position.CartesianPosition.Y = 0.0;
	command.Position.CartesianPosition.Z = 0.15;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = 0.0;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendBasicTrajectory)(command);
	Sleep(30);
}

void MoveDown() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl; return;
	}
	
	TrajectoryPoint command;

	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;

	command.Position.CartesianPosition.X = 0.0;
	command.Position.CartesianPosition.Y = 0.0;
	command.Position.CartesianPosition.Z = - 0.15;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = 0.0;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendAdvanceTrajectory)(command);
	Sleep(30);
}

void MoveIn() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl; return;
	}
	
	TrajectoryPoint command;

	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;

	command.Position.CartesianPosition.X = 0.0;
	command.Position.CartesianPosition.Y = 0.15;
	command.Position.CartesianPosition.Z = 0.0;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = 0.0;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendBasicTrajectory)(command);
	Sleep(30);
}

void MoveOut() {
	if (!homePositionSet) {
		cout << "Call MoveHome() First" << endl; return;
	}
	
	TrajectoryPoint command;

	command.InitStruct();
	command.Position.Type = CARTESIAN_VELOCITY;

	command.Position.CartesianPosition.X = 0.0;
	command.Position.CartesianPosition.Y = - 0.15;
	command.Position.CartesianPosition.Z = 0.0;
	command.Position.CartesianPosition.ThetaX = 0.0;
	command.Position.CartesianPosition.ThetaY = 0.0;
	command.Position.CartesianPosition.ThetaZ = 0.0;
	command.Position.HandMode = HAND_NOMOVEMENT;

	// CARTESIAN_VELOCITY requires repeated sends — 200 x 5ms = 1 second of motion
	(*MySendAdvanceTrajectory)(command);
	Sleep(30);
}


void Shervins_Home() {
	


	MySetAngularControl();
	MyEraseAllTrajectories();

	TrajectoryPoint point;
	memset(&point, 0, sizeof(point));
	
	point.InitStruct();
	point.Position.Type = ANGULAR_POSITION;

	point.Position.Actuators.Actuator1 = home[0];
	point.Position.Actuators.Actuator2 = home[1];
	point.Position.Actuators.Actuator3 = home[2];
	point.Position.Actuators.Actuator4 = home[3];
	point.Position.Actuators.Actuator5 = home[4];
	point.Position.Actuators.Actuator6 = home[5];
	point.Position.Actuators.Actuator7 = home[6];

	(*MySendAdvanceTrajectory)(point);

	homePositionSet = true;

	MySetCartesianControl();

	Sleep(2000);
	return;
}


void Shervins_Rest() {
	if (!homePositionSet) {
		cout << "Call Shervins_Home First" << endl;
		return;
	}


	MySetAngularControl();
	MyEraseAllTrajectories();

	TrajectoryPoint command;
	memset(&command, 0, sizeof(command));

	command.InitStruct();
	command.Position.Type = ANGULAR_POSITION;

	command.Position.Actuators.Actuator1 = rest[0];
	command.Position.Actuators.Actuator2 = rest[1];
	command.Position.Actuators.Actuator3 = rest[2];
	command.Position.Actuators.Actuator4 = rest[3];
	command.Position.Actuators.Actuator5 = rest[4];
	command.Position.Actuators.Actuator6 = rest[5];
	command.Position.Actuators.Actuator7 = rest[6];

	(*MySendAdvanceTrajectory)(command);

	MySetCartesianControl();
	Sleep(2000);
	return;
}





