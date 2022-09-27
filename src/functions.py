
import os, json, logging
from structs import *


def updateDataFile(newData, dataPath, fileID):
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
	logging.debug(f"{dataPath}/{fileID} data updated")

def updateGuildData(newData, fileID): updateDataFile(newData, "guilds", fileID)
def updateUserData (newData, fileID): updateDataFile(newData, "users",  fileID)


def getDataFile(dataPath, fileID):
	filePath = os.path.abspath(f"{CONFIG.DATA_DIR}/{dataPath}/{fileID}.json")
	if not os.path.exists(filePath): return dict()

	logging.debug(f"{dataPath}/{fileID} data read")
	with open(filePath, "r") as fobj: fileData = json.load(fobj)
	

def getGuildData(fileID): getDataFile("guilds", fileID)
def getUserData (fileID): getDataFile("users",  fileID)


async def executeCommand(message):
	command = message.content.replace(COMMAND.PREFIX, "", 1).split(" ")[0]
	content = message.content.replace(COMMAND.PREFIX+command, "", 1)
	
	logging.debug(f"(execute command) {command}")
	await COMMAND.DICT.get(command, COMMAND.DICT["unknowCommand"])([object, message, command, content])
