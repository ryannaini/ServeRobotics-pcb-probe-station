/*****************************************************************************************************/
/*                                                                                                   */
/* Uses the 7 dof robot and Ethernet in Cartesian mode                                               */
/*                                                                                                   */
/*****************************************************************************************************/

#ifndef UNICODE
#define UNICODE
#endif

#include <iostream>
#include <vector>
#include "KinovaTypes.h"
#include "robot.h"

#ifdef __linux__
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>
#include "Kinova.API.EthCommLayerUbuntu.h"
#include "Kinova.API.EthCommandLayerUbuntu.h"
#elif defined(_WIN32) || defined(_WIN64)
#include <windows.h>
#include "CommunicationLayer.h"
#include "CommandLayer.h"
#endif
#include "movements.h"

using namespace std;

int main(int argc, char* argv[])
{
	int result;

	result = InitializeRobot();

	cout << "Did it move?" << endl;




	Sleep(6);

	Shervins_Rest();

	bool end = CleanupRobot();

}
