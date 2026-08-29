// _______________________________________________
//
// Initializing the robot so main.cpp calls it once and keeps the 
// program running once 
// 
// -----------------------------------------------

#ifndef UNICODE
#define UNICODE
#endif

#include <iostream>
#include <fstream>
#include "robot.h"
#include "movements.h"


using namespace std;


// =====
// Global Variable 
// =====

HINSTANCE	commandLayer_handle; // Command layer able to reach to the .dll files 

int(*MyInitAPI)() =																	nullptr;
int(*MyCloseAPI)() =																nullptr;
int(*MyRefresDevicesList)() =														nullptr;

int(*MyGetDevices)(KinovaDevice devices[MAX_KINOVA_DEVICE], int& result) =			nullptr;
int(*MySetActiveDevice)(KinovaDevice device) =										nullptr;
int(*MyGetActualTrajectoryInfo)(TrajectoryFIFO& response) =							nullptr;
int(*MyEraseAllTrajectories)() =													nullptr;

int(*MyInitFingers)() =																nullptr;
int(*MySendBasicTrajectory)(TrajectoryPoint trajectory) =							nullptr;
int(*MySendAdvanceTrajectory)(TrajectoryPoint trajectory) =							nullptr;
int(*MyMoveHome)() =																nullptr;

int(*MySetCartesianControl)() =														nullptr;
int(*MyGetCartesianPosition)(CartesianPosition& pt) =								nullptr;

int(*MySetAngularControl)() =														nullptr;
int(*MyGetAngularPosition)(AngularPosition& pt) =									nullptr;

int(*MyEraseAllProtectionZones)() =													nullptr;
int(*MyGetProtectionZone)(ZoneList& response) =										nullptr;
int(*MyActivateSingularityAutomaticAvoidance)(int& state) =							nullptr;
int(*MyGetSystemErrorCount)(unsigned int& response) =								nullptr;
int(*MyGetSensorsInfo)(SensorsInfo& response) =										nullptr;
int(*MyActivateCollisionAvoidance)(int& state) =									nullptr;
int(*MyGetSystemError)(unsigned int indexError, SystemError& response) =			nullptr;
int(*MyGetControlType)(int& mode) =														nullptr;

int InitializeRobot() {


	commandLayer_handle = LoadLibrary(L"CommandLayerEthernet.dll");
	
	if (!commandLayer_handle) return 0;


	MyInitAPI = (int(*)())											GetProcAddress(commandLayer_handle, "InitAPI");
	MyCloseAPI = (int(*)())											GetProcAddress(commandLayer_handle, "CloseAPI");
	MyRefresDevicesList = (int(*)())								GetProcAddress(commandLayer_handle, "RefresDevicesList");
	MyMoveHome = (int(*)())											GetProcAddress(commandLayer_handle, "MoveHome");
	MyInitFingers = (int(*)())										GetProcAddress(commandLayer_handle, "InitFingers");
	MyGetActualTrajectoryInfo = (int(*)(TrajectoryFIFO & response))	GetProcAddress(commandLayer_handle, "GetActualTrajectoryInfo");
	MyEraseAllTrajectories = (int(*)())								GetProcAddress(commandLayer_handle, "EraseAllTrajectories");
	MySetCartesianControl = (int(*)())								GetProcAddress(commandLayer_handle, "SetCartesianControl");
	MySetAngularControl = (int(*)())								GetProcAddress(commandLayer_handle, "SetAngularControl");
	MySendBasicTrajectory = (int(*)(TrajectoryPoint trajectory))	GetProcAddress(commandLayer_handle, "SendBasicTrajectory");
	MySendAdvanceTrajectory = (int(*)(TrajectoryPoint trajectory))	GetProcAddress(commandLayer_handle, "SendAdvanceTrajectory");
	MyGetCartesianPosition = (int(*) (CartesianPosition & pt))		GetProcAddress(commandLayer_handle, "GetCartesianPosition");
	MyGetAngularPosition = (int(*) (AngularPosition & pt))			GetProcAddress(commandLayer_handle, "GetAngularPosition");
	MyGetDevices = (int(*)(KinovaDevice devices[MAX_KINOVA_DEVICE], int& result)) GetProcAddress(commandLayer_handle, "GetDevices");
	MyEraseAllProtectionZones = (int(*)())							GetProcAddress(commandLayer_handle, "EraseAllProtectionZones");
	MyGetProtectionZone = (int(*)(ZoneList&))						GetProcAddress(commandLayer_handle, "GetProtectionZone");
	MySetActiveDevice = (int(*)(KinovaDevice devices))				GetProcAddress(commandLayer_handle, "SetActiveDevice");
	MyActivateSingularityAutomaticAvoidance = (int(*)(int&))		GetProcAddress(commandLayer_handle, "ActivateSingularityAutomaticAvoidance");
	MyGetSystemErrorCount = (int(*)(unsigned int&))					GetProcAddress(commandLayer_handle, "GetSystemErrorCount");
	MyGetSensorsInfo = (int(*)(SensorsInfo&))						GetProcAddress(commandLayer_handle, "GetSensorsInfo");
	MyActivateCollisionAvoidance = (int(*)(int&))					GetProcAddress(commandLayer_handle, "ActivateCollisionAutomaticAvoidance");
	MyGetSystemError = (int(*)(unsigned int, SystemError&))			GetProcAddress(commandLayer_handle, "GetSystemError");
	MyGetControlType = (int(*)(int&))								GetProcAddress(commandLayer_handle, "GetControlType");


	// Check all pointers resolved
	bool anyNull = false;

	if (MyInitAPI == nullptr)									{ cout << "  [NULL] MyInitAPI" << endl; anyNull = true; }
	if (MyCloseAPI == nullptr)									{ cout << "  [NULL] MyCloseAPI" << endl; anyNull = true; }
	if (MyRefresDevicesList == nullptr)							{ cout << "  [NULL] MyRefresDevicesList" << endl; anyNull = true; }
	if (MyGetDevices == nullptr)								{ cout << "  [NULL] MyGetDevices" << endl; anyNull = true; }
	if (MySetActiveDevice == nullptr)							{ cout << "  [NULL] MySetActiveDevice" << endl; anyNull = true; }
	if (MyGetActualTrajectoryInfo == nullptr)					{ cout << "  [NULL] MyGetActualTrajectoryInfo" << endl; anyNull = true; }
	if (MyEraseAllTrajectories == nullptr)						{ cout << "  [NULL] MyEraseAllTrajectories" << endl; anyNull = true; }
	if (MyInitFingers == nullptr)								{ cout << "  [NULL] MyInitFingers" << endl; anyNull = true; }
	if (MySendBasicTrajectory == nullptr)						{ cout << "  [NULL] MySendBasicTrajectory" << endl; anyNull = true; }
	if (MySendAdvanceTrajectory == nullptr)						{ cout << "  [NULL] MySendAdvanceTrajectory" << endl; anyNull = true; }
	if (MyMoveHome == nullptr)									{ cout << "  [NULL] MyMoveHome" << endl; anyNull = true; }
	if (MySetCartesianControl == nullptr)						{ cout << "  [NULL] MySetCartesianControl" << endl; anyNull = true; }
	if (MyGetCartesianPosition == nullptr)						{ cout << "  [NULL] MyGetCartesianPosition" << endl; anyNull = true; }
	if (MySetAngularControl == nullptr)							{ cout << "  [NULL] MySetAngularControl" << endl; anyNull = true; }
	if (MyGetAngularPosition == nullptr)						{ cout << "  [NULL] MyGetAngularPosition" << endl; anyNull = true; }
	if (MyEraseAllProtectionZones == nullptr)					{ cout << "  [NULL] MyEraseAllProtectionZones" << endl; anyNull = true; }
	if (MyGetProtectionZone == nullptr)							{ cout << "  [NULL] MyGetProtectionZone" << endl; anyNull = true; }
	if (MyActivateSingularityAutomaticAvoidance == nullptr)		{ cout << "  [NULL] MyActivateSingularityAutomaticAvoidance" << endl; anyNull = true; }
	if (MyGetSystemErrorCount == nullptr)						{ cout << "  [NULL] MyGetSystemErrorCount" << endl; anyNull = true; }
	if (MyGetSensorsInfo == nullptr)							{ cout << "  [NULL] MyGetSensorsInfo" << endl; anyNull = true; }
	if (MyActivateCollisionAvoidance == nullptr)				{ cout << "  [NULL] MyActivateCollisionAvoidance" << endl; anyNull = true; }
	if (MyGetSystemError == nullptr)							{ cout << "  [NULL] MyGetSystemError" << endl; anyNull = true; }
	if (MyGetControlType == nullptr)							{ cout << "  [NULL] MyGetControlType" << endl; anyNull = true; }
	if (anyNull)
	{
		cout << "* * *  E R R O R   D U R I N G   I N I T I A L I Z A T I O N  * * *" << endl;
		cout << "One or more function pointers failed to resolve." << endl;
		return false;
	}
	cout << "All function pointers resolved." << endl;

	int result = MyInitAPI(); // InitAPI get's called

	if (result == 0) { cout << "*** ERROR Initialization Failed (InitAPI Call Failed)" << endl; return result;  }


	cout << "API RESULT: " << result << endl;

	int refresh = (*MyRefresDevicesList)(); // Ignoring return value 

	cout << "RefreshDevice: " << refresh << endl;

	KinovaDevice list[MAX_KINOVA_DEVICE];

	int devicesCount = (*MyGetDevices)(list, result); // Identical to MyGetDevices(list, result)

	if (devicesCount != 1) { cout << "*** ERROR: Robot not found, device count is: " << devicesCount << endl; return 0; }


	cout << "Serial Number: " << list[0].SerialNumber << endl;
	cout << "Model: " << list[0].Model << endl;
	cout << "Device ID: " << list[0].DeviceID << endl;


	int result_device = MySetActiveDevice(list[0]); 

	if (result_device == 0) { cout << "*** ERROR: Robot not in the first index of the list" << endl; return 0; }

	Shervins_Home(); // moving to custom pre-built home with desired angular needs 

	Sleep(1000);

	cout << "Robot Initialization complete" << endl;

	MySetCartesianControl();

	return result;
}

void myCurrentLocation() {
	CartesianPosition position;

	MyGetCartesianPosition(position);

	cout << position.Coordinates.X << " "
		<< position.Coordinates.Y << " "
		<< position.Coordinates.Z << " "
		<< position.Coordinates.ThetaX << " "
		<< position.Coordinates.ThetaY << " "
		<< position.Coordinates.ThetaZ << " "
		<< endl;
}


bool CleanupRobot() {

	if (!commandLayer_handle) return false;

	if (MyCloseAPI) MyCloseAPI();
	FreeLibrary(commandLayer_handle);
	commandLayer_handle = NULL;
	return true;

}
