#pragma once

// =============================================================
// robot.h
// =============================================================
// PURPOSE:
//   Declares all global function pointers loaded from
//   CommandLayerEthernet.dll and exposes InitializeRobot()
//   and CleanupRobot() for use across the project.
// 
//   Note: This is such that the dll files are initialized once and not called 
//		   everytime a function is called and re-called.
//
//   The DLL is loaded ONCE at startup via InitializeRobot()
//   and unloaded ONCE at shutdown via CleanupRobot().
//   All other files (movements.cpp, main.cpp) access the
//   robot through these shared function pointers.
//
// DEPENDENCIES:
//   - KinovaTypes.h  : EthernetCommConfig, KinovaDevice,
//                      CartesianPosition, TrajectoryPoint
//   - windows.h      : HINSTANCE, LoadLibrary, GetProcAddress
//   - Ws2_32.lib     : inet_addr for IP address conversion
//
// USAGE:
//   1. Call InitializeRobot() once at program startup
//   2. Use function pointers directly in any file that includes robot.h
//   3. Call CleanupRobot() once before program exits
//
// EXAMPLE:
//   #include "robot.h"
//   InitializeRobot();
//   MySendBasicTrajectory(point);
//   CleanupRobot();
// =============================================================



#include <windows.h>
#include <KinovaTypes.h>
#include "CommandLayer.h"
#include "CommunicationLayer.h"
#include <vector>

// =============================================================
//
// Note: The only thing necessary in the header file is the declare
//		 the pointer variables necessary in robot.cpp
//
// =============================================================



extern int(*MyInitAPI)();                // Initialization API Call, successfull if the API is able to be loaded
extern int(*MyCloseAPI)();                // Closing of the API 
extern int(*MyRefresDevicesList)();        // Refreshes/re-scans for robots without restarting the API    

extern int(*MyGetDevices)(KinovaDevice devices[MAX_KINOVA_DEVICE], int& result); // Scans (in ETHERNET) for all connected Kinova robots
																				// with a returing list of them with a count  
extern int(*MySetActiveDevice)(KinovaDevice device);                             // Picks which of the following list of robots to control
extern int(*MyGetActualTrajectoryInfo)(TrajectoryFIFO& response);                 // Hopefully get's livetime info of the trajectory of the robot 
extern int(*MyEraseAllTrajectories)();

extern int(*MyInitFingers)();            // Most Likely do not need this as no fingers
extern int(*MySendBasicTrajectory)(TrajectoryPoint trajectory);        // Sends a SINGLE trajectory point to the robot- works for both 
																		// CARTESIAN_POSITION & CARTESIAN_VELOCITY
extern int(*MySendAdvanceTrajectory)(TrajectoryPoint trajectory);    // Sends a PRE-PLANNED sequence of trajectory points - for complex
																	// multi-step paths queued up in advance 
extern int(*MyMoveHome)();

extern int(*MySetCartesianControl)();    // Switches the robot into Cartesian Mode - accepts XYZ position/velocity commands
extern int(*MyGetCartesianPosition)(CartesianPosition& pt);         // Reads the physical position of the end effector (XYZ)

extern int(*MySetAngularControl)();        // Switches the robot into Angular Control - accepts joint-by-joint angle commands
extern int(*MyGetAngularPosition)(AngularPosition& pt);                // Reads the joint angles of each joint currently in degrees

extern int(*MyEraseAllProtectionZones)();
extern int(*MyGetProtectionZone)(ZoneList& response);
extern int(*MyActivateSingularityAutomaticAvoidance)(int& state);
extern int(*MyGetSystemErrorCount)(unsigned int& response);
extern int(*MyGetSensorsInfo)(SensorsInfo& response);
extern int(*MyActivateCollisionAvoidance)(int& state);
extern int(*MyGetSystemError)(unsigned int indexError, SystemError& response);
extern int(*MyGetControlType)(int& mode);

int InitializeRobot();						// My Function, Wrapping this all up in a clean initialize robot function that gets called in main.cpp
void myCurrentLocation();		// My Function, Returning the Current Coordinates and putting them into a vector 
bool CleanupRobot();						// My Function, Wrapping this all up in a clean Closing Function for main.cpp to call once 



