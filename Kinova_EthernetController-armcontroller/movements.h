#pragma once 
// =============================================================
// movements.h
// 
// 
// 
// By: Shervin Naini
// For: Serve Robotics 
// =============================================================
// PURPOSE:
//   Declares all robot movement functions for the Kinova Gen2 arm.
//   Acts as the "menu" — any file that includes this knows what
//   movements exist and how to call them, without knowing how
//   they are implemented (that lives in movements.cpp).
//
// DEPENDENCIES:
//   - movements.cpp includes robot.h that essentially handles the dll
//	   loading and connections to acces the Global Functions 
//     pointers (MySendBasicTrajectory, MyGetCartesianCommand)
//   - This file does NOT include Kinova headers directly
// 
// USAGE EXAMPLES:
// 1. MoveToHome();			// Returns the Robot to home position 



/* @Note: This header is NOT a class as the functions do not hold any data or 
/* hold multiple instances */



// ===================================================
//
// GLOBAL POINTER CONTROL FUNCTIONS FROM DLL FILE
//
// ===================================================


#include "robot.h"
#include "KinovaTypes.h"
#include <windows.h>
#include <iostream>


/* ALL Descriptions are in movements.cpp */
//bool MoveHome(int &result);

void MoveRight();

void MoveLeft();

void MoveDown();

void MoveUp();

void MoveIn();

void MoveOut();

void Shervins_Home(); // desired angular positions for home 

void Shervins_Rest(); // desired angular position for rest 

//void MovingtoHome();


