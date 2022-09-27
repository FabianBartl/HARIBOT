
import os, json, logging
from  structs import *


def updateDataFile(newData, dataPath, fileID):
	filePath = os.path.abspath(f"{CONFIG.DATA_DIR}/{dataPath}/{fileID}.json")

	if not os.path.exists(filePath):
		with open(filePath, "w+") as fobj:
			fobj.write("{}")

	with open(filePath, "r") as fobj:
		oldData = json.load(fobj)
	
	for key in newData:
		if   len(newData[key]) == 1: value, mode = newData[key], "new"
		elif len(newData[key]) == 2: value, mode = newData[key]

		if key not in oldData: mode = "new"

		if   mode == "add": oldData[key] += value
		elif mode == "sub": oldData[key] -= value
		elif mode == "mul": oldData[key] *= value
		elif mode == "div": oldData[key] /= value

		elif mode == "new": oldData[key]  = value
		else:               oldData[key]  = value
	
	with open(filePath, "w") as fobj:
		json.dump(oldData, fobj)
	
	logging.debug(f"{dataPath} data updated")

def updateGuildData(newData, fileID): updateDataFile(newData, "guilds", fileID)
def updateUserData (newData, fileID): updateDataFile(newData, "users",  fileID)


def executeCommand(clientObj, message):
	pass
