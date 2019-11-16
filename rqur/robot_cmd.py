import sys
import urx
from urx.robotiq_two_finger_gripper import Robotiq_Two_Finger_Gripper
from urx.robot import Robot
from urx.robot import URRobot

if __name__ == '__main__':
	rob = URRobot("10.20.0.194")
	rob.movex()
