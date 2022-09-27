
import os, json, logging
from structs import CONFIG

#-------------#
# update data #
#-------------#

def updateDataFile(newData: dict, dataPath: str, fileID: int) -> None:
	filePath = os.path.abspath(f"{CONFIG.DATA_DIR}/{dataPath}/{fileID}.json")

	if not os.path.exists(filePath): fileData = {}
	else:
		with open(filePath, "r") as fobj: fileData = json.load(fobj)
	
	for key in newData:
		if   len(newData[key]) == 1: value, mode = newData[key], "new"
		elif len(newData[key]) == 2: value, mode = newData[key]

		if key not in fileData: mode = "new"

		if   mode == "add": fileData[key] += value
		elif mode == "sub": fileData[key] -= value
		elif mode == "mul": fileData[key] *= value
		elif mode == "div": fileData[key] /= value
		elif mode == "new": fileData[key]  = value
	
	with open(filePath, "w+") as fobj: json.dump(fileData, fobj)
	logging.debug(f"{dataPath}/{fileID} data updated: {fileData}")

def updateGuildData(newData: dict, fileID: int) -> None: updateDataFile(newData, "guilds", fileID)
def updateUserData (newData: dict, fileID: int) -> None: updateDataFile(newData, "users",  fileID)

#----------#
# get data #
#----------#

def getDataFile(dataPath: str, fileID: int) -> dict:
	filePath = os.path.abspath(f"{CONFIG.DATA_DIR}/{dataPath}/{fileID}.json")
	if not os.path.exists(filePath): return dict()

	logging.debug(f"{dataPath}/{fileID} data read")
	with open(filePath, "r") as fobj: return json.load(fobj)
	

def getGuildData(fileID: int) -> dict: return getDataFile("guilds", fileID)
def getUserData (fileID: int) -> dict: return getDataFile("users",  fileID)
