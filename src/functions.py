
import os, json, logging, re
from structs import CONFIG, DATABASE

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

def updateGuildData    (newData: dict, fileID: int) -> None: updateDataFile(newData, "guilds",    fileID)
def updateUserData     (newData: dict, fileID: int) -> None: updateDataFile(newData, "users",     fileID)
def updateReactionsData(newData: dict, fileID: int) -> None: updateDataFile(newData, "reactions", fileID)

#----------#
# get data #
#----------#

def getDataFile(dataPath: str, fileID: int) -> dict:
	cursor = DATABASE.CURSOR

	filePath = os.path.abspath(f"{CONFIG.DATA_DIR}/{dataPath}/{fileID}.json")
	if not os.path.exists(filePath): return dict()

	logging.debug(f"{dataPath}/{fileID} data read")
	with open(filePath, "r") as fobj: return json.load(fobj)

def getGuildData    (fileID: int) -> dict: return getDataFile("guilds",    fileID)
def getUserData     (fileID: int) -> dict: return getDataFile("users",     fileID)
def getReactionsData(fileID: int) -> dict: return getDataFile("reactions", fileID)

#---------------------#
# manage logging file #
#---------------------#

def getLogFile(srcPath: str=CONFIG.LOG_FILE, length: int=20) -> str:
	with open(CONFIG.LOG_FILE, "r") as fobj: lines = fobj.readlines()
	
	log_data = list()
	for line in lines[len(lines)-length:]:
		re.sub("(\t|\n)+", "\t", line)
		if len(line) < 100: log_data.append(line)
		else:               log_data.append(f"{line[:100]}...")
	
	return "".join(log_data)


def saveLogFile(dstPAth: str, srcPath: str=CONFIG.LOG_FILE) -> int:
	with open(srcPath, "r") as fsrc:
		with open(dstPAth, "w+") as fdst:
			destLines = fsrc.readlines()
			destSize = len(destLines)
			fdst.writelines(destLines)
	return destSize


def clearLogFile(srcPath: str=CONFIG.LOG_FILE) -> None:
	with open(CONFIG.LOG_FILE, "w+") as fobj: pass
