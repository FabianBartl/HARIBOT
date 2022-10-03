
import os, json, re
from colorama import Fore, Back, Style

from structs import CONFIG, TOKEN, LOG
import custom_logger

#----------------#
# help functions #
#----------------#

def formatBytes(num: int, step: int=1000):
	for unit in " KMGT":
		if num < step: return f"{num:3.2f} {unit}B"
		num /= step
#-------------#
# update data #
#-------------#

def updateDataFile(newData: dict, dataPath: str, fileID: int) -> None:
	filePath = os.path.abspath(os.path.join(CONFIG.DATA_DIR, dataPath, f"{fileID}.json"))

	if not os.path.exists(filePath): fileData = {}
	else:
		with open(filePath, "r") as fobj: fileData = json.load(fobj)
	
	for key in newData:
		if   len(newData[key]) == 1: value, mode = newData[key], "set"
		elif len(newData[key]) == 2: value, mode = newData[key]

		if key not in fileData: mode = "set"

		if   mode == "add": fileData[key] += value
		elif mode == "sub": fileData[key] -= value
		elif mode == "mul": fileData[key] *= value
		elif mode == "div": fileData[key] /= value
		elif mode == "set": fileData[key]  = value
	
	with open(filePath, "w+") as fobj: json.dump(fileData, fobj)
	LOG.LOGGER.debug(f"{dataPath}/{fileID} data updated: {fileData}")

def updateGuildData   (newData: dict, fileID: int) -> None: updateDataFile(newData, "guilds",    fileID)
def updateUserData    (newData: dict, fileID: int) -> None: updateDataFile(newData, "users",     fileID)
def updateReactionData(newData: dict, fileID: int) -> None: updateDataFile(newData, "reactions", fileID)

#----------#
# get data #
#----------#

def getDataFile(dataPath: str, fileID: int) -> dict:
	filePath = os.path.abspath(os.path.join(CONFIG.DATA_DIR, dataPath, f"{fileID}.json"))
	if not os.path.exists(filePath): return dict()
	with open(filePath, "r") as fobj: data = json.load(fobj)
	LOG.LOGGER.debug(f"{dataPath}/{fileID} data read")
	return data

def getGuildData   (fileID: int) -> dict: return getDataFile("guilds",    fileID)
def getUserData    (fileID: int) -> dict: return getDataFile("users",     fileID)
def getReactionData(fileID: int) -> dict: return getDataFile("reactions", fileID)

#------------------#
# check permissons #
#------------------#

def checkOwner(checkID: int) -> bool: return checkID == TOKEN.OWNER_ID

#------------------------#
# manage logging (files) #
#------------------------#

def setupLogger(colored: bool=False):
	LOG.LOGGER = custom_logger.getLogger(init=True, level=LOG.LEVEL, fmt=LOG.FMT, date_fmt=LOG.DATE_FMT, path=LOG.PATH, colored=colored)
	return LOG.LOGGER

def getLogFile(srcPath: str=LOG.PATH, rows: int=21) -> str:
	with open(LOG.PATH, "r") as fobj: lines = fobj.readlines()
	
	max_chars = 1900
	length = max_chars // rows
	log_data = list()

	for line in lines[len(lines)-rows:]:
		line = line[11:]
		line = re.sub(",[0-9]+ \|",     " |", line)
		line = re.sub("\| *DEBUG \|",    "D", line)
		line = re.sub("\| *INFO \|",     "I", line)
		line = re.sub("\| *WARNING \|",  "W", line)
		line = re.sub("\| *ERROR \|",    "E", line)
		line = re.sub("\| *CRITICAL \|", "C", line)
		line = re.sub("(\t|\n| )+",      " ", line)

		if len(line) <= length: log_data.append(f"{line}\n")
		else:                   log_data.append(f"{line[:length-3]}...\n")
	
	LOG.LOGGER.debug(f"returned end of log file")
	return "".join(log_data)[:max_chars]

def saveLogFile(dstPath: str, srcPath: str=LOG.PATH) -> int:
	with open(srcPath, "r") as fsrc:
		with open(dstPath, "w+") as fdst:
			destLines = fsrc.readlines()
			destSize = len(destLines)
			fdst.writelines(destLines)
	LOG.LOGGER.info(f"log file saved at {dstPath}")
	return destSize

def clearLogFile(srcPath: str=LOG.PATH) -> None:
	with open(srcPath, "w+") as fobj: pass
	LOG.LOGGER.info(f"file `{srcPath}` cleared")

def resetLogFiles(logDir: str=LOG.DIR, logPath: str=LOG.PATH) -> list[str, ]:
	logFiles = os.listdir(os.path.abspath(logDir))
	for file in logFiles:
		filePath = os.path.join(logDir, file)

		if filePath == logPath:
			clearLogFile(logPath)
			LOG.LOGGER.info(f"file `{filePath}` cleared")
		else:
			os.remove(filePath)
			LOG.LOGGER.warning(f"file `{filePath}` deleted")
	
	return logFiles

def backupLogFile(dstPath: str, srcPath: str=LOG.PATH, *args) -> tuple[str, int]:
	log_code = getLogFile(srcPath, *args)
	destSize = saveLogFile(dstPath, srcPath)
	clearLogFile(srcPath)
	LOG.LOGGER.info(f"log file backuped at {dstPath}")
	return log_code, destSize
