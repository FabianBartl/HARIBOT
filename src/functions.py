
import os, json, logging, re
from structs import CONFIG, DATABASE, TOKEN, LOG

#-------------#
# update data #
#-------------#

def updateDataFile(newData: dict, dataPath: str, fileID: int) -> None:
	filePath = os.path.abspath(os.path.join(CONFIG.DATA_DIR, dataPath, f"{fileID}.json"))

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

def updateGuildData   (newData: dict, fileID: int) -> None: updateDataFile(newData, "guilds",    fileID)
def updateUserData    (newData: dict, fileID: int) -> None: updateDataFile(newData, "users",     fileID)
def updateReactionData(newData: dict, fileID: int) -> None: updateDataFile(newData, "reactions", fileID)

#----------#
# get data #
#----------#

def getDataFile(dataPath: str, fileID: int) -> dict:
	cursor = DATABASE.CURSOR

	filePath = os.path.abspath(os.path.join(CONFIG.DATA_DIR, dataPath, f"{fileID}.json"))
	if not os.path.exists(filePath): return dict()

	logging.debug(f"{dataPath}/{fileID} data read")
	with open(filePath, "r") as fobj: return json.load(fobj)

def getGuildData   (fileID: int) -> dict: return getDataFile("guilds",    fileID)
def getUserData    (fileID: int) -> dict: return getDataFile("users",     fileID)
def getReactionData(fileID: int) -> dict: return getDataFile("reactions", fileID)

#------------------#
# check permissons #
#------------------#

def checkOwner(checkID: int) -> bool: return checkID == TOKEN.OWNER_ID

#---------------------#
# manage logging file #
#---------------------#

def getLogFile(srcPath: str=LOG.PATH, rows: int=21) -> str:
	with open(LOG.PATH, "r") as fobj: lines = fobj.readlines()
	
	length = 2000 // rows
	log_data = list()

	for line in lines[len(lines)-rows:]:

		line = re.sub("(\t|\n)+", " ", line[11:])
		line = line.replace(" [DEBUG]",    "D")
		line = line.replace(" [INFO]",     "I")
		line = line.replace(" [WARNING]",  "W")
		line = line.replace(" [CRITICAL]", "C")
		line = line.replace(" [ERROR]",    "E")

		if len(line) <= length: log_data.append(f"{line}\n")
		else:                   log_data.append(f"{line[:length-3]}...\n")
	
	return "".join(log_data)[:2000-10]

def saveLogFile(dstPAth: str, srcPath: str=LOG.PATH) -> int:
	with open(srcPath, "r") as fsrc:
		with open(dstPAth, "w+") as fdst:
			destLines = fsrc.readlines()
			destSize = len(destLines)
			fdst.writelines(destLines)
	return destSize

def clearLogFile(srcPath: str=LOG.PATH) -> None:
	with open(LOG.PATH, "w+") as fobj: pass

def resetLogFiles(logDir: str=LOG.DIR, logPath: str=LOG.PATH) -> list[str, ]:
	logFiles = os.listdir(os.path.abspath(logDir))

	for file in logFiles:
		filePath = os.path.join(logDir, file)

		if filePath == logPath:
			clearLogFile(logPath)
			logging.info(f"file `{filePath}` cleared")
		else:
			os.remove(filePath)
			logging.warning(f"file `{filePath}` deleted")
	
	return logFiles

def backupLogFile(dstPath: str, srcPath: str=LOG.PATH, *args) -> tuple[str, int]:
	log_code = getLogFile(srcPath, *args)
	destSize = saveLogFile(dstPath, srcPath)
	clearLogFile(srcPath)
	return log_code, destSize
