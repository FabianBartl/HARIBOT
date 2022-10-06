
# libs
import nextcord
from nextcord import Member

import os, json, re, logging
from math import floor

from structs import TOKEN, LOG, DIR, COLOR, XP
import custom_logger

#----------------#
# format numbers #
#----------------#

def formatNum(num: int, step: int=1000, base_unit: str="") -> str:
	for unit in " KMGT":
		if num < step: break
		num /= step
	return f"{num:3.2f} {unit}{base_unit}"

def formatBytes(num: int, step: int=1000) -> str: return formatNum(num, step, "B")

def hex2color(num: int, mode: str="hex") -> str:
	if   mode == "hex": return hex2color(int(f"{hex(num)}ff", 16), "hexa")
	elif mode == "rgb": return hex2color(int(f"{hex(num)}ff", 16), "rgba")
	elif mode == "hexa": return f"#{hex(num)[2:10]}"
	elif mode == "rgba":
		h = hex(num)
		return f"rgba({h[2:4]}, {h[4:6]}, {h[6:8]}, {h[8:10]})"

#----------------#
# help functions #
#----------------#

def svg2png(svgFile: str, pngFile: str, width: int) -> int:
	return os.system(f"{os.path.join(DIR.APPS, 'inkscape', 'InkscapePortable.exe')} --without-gui '{os.path.abspath(svgFile)}' -w {width} -o '{os.path.abspath(pngFile)}'")

#-------------#
# update data #
#-------------#

def updateDataFile(newData: dict, dataPath: str, fileID: int) -> None:
	filePath = os.path.abspath(os.path.join(DIR.DATA, dataPath, f"{fileID}.json"))

	if not os.path.exists(filePath): fileData = {}
	else:
		with open(filePath, "r") as fobj: fileData = json.load(fobj)
	
	for key in newData:
		value, mode = newData[key]

		if key in fileData:
			# <int>, <float>
			if   mode == "add": fileData[key] += value
			elif mode == "sub": fileData[key] -= value
			elif mode == "min": fileData[key] = min(fileData[key], value)
			elif mode == "max": fileData[key] = max(fileData[key], value)
			# <list>
			elif mode == "ext": fileData[key].append(value)
			elif mode == "ins":
				if value not in fileData[key]: fileData[key].append(value)
			elif mode == "rem": 
				if value in fileData[key]: del fileData[key][fileData[key].index(value)]
			# <Any>
			elif mode == "set": fileData[key] = value
			elif mode == "del": del fileData[key]
		
		else:
			# <int>, <float>
			if   mode == "add": fileData[key] = value
			elif mode == "sub": fileData[key] = -value
			elif mode == "min": fileData[key] = value
			elif mode == "max": fileData[key] = value
			# <list>
			elif mode == "ext": fileData[key] = [value]
			elif mode == "ins": fileData[key] = [value]
			elif mode == "rem": pass
			# <Any>
			elif mode == "set": fileData[key] = value
			elif mode == "del": pass
	
	with open(filePath, "w+") as fobj: json.dump(fileData, fobj)
	LOG.LOGGER.debug(f"{dataPath}/{fileID} data updated: {fileData}")

def updateGuildData   (newData: dict, fileID: int) -> None: updateDataFile(newData, "guilds",    fileID)
def updateUserData    (newData: dict, fileID: int) -> None: updateDataFile(newData, "users",     fileID)
def updateReactionData(newData: dict, fileID: int) -> None: updateDataFile(newData, "reactions", fileID)

#----------#
# get data #
#----------#

def getDataFile(dataPath: str, fileID: int) -> dict:
	filePath = os.path.abspath(os.path.join(DIR.DATA, dataPath, f"{fileID}.json"))
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

def setupLogger(colored: bool=False, level: int=logging.INFO):
	LOG.LOGGER = custom_logger.getLogger(init=True, level=level, fmt=LOG.FMT, date_fmt=LOG.DATE_FMT, path=LOG.PATH, colored=colored)
	return LOG.LOGGER

def getLogFile(srcPath: str=LOG.PATH, rows: int=21) -> str:
	with open(LOG.PATH, "r") as fobj: lines = fobj.readlines()
	
	max_chars = 1_900
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
			destSize = len("\n".join(destLines))
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

#-------------------------------------------#
# score / level / ranking / badge functions #
#-------------------------------------------#

def createScoreCard(member: Member): #-> lambda-function
	user_data = getUserData(member.id)

	xp_current         = user_data.get("xp", 0)
	level_current      = XP.LEVEL(xp_current)
	xp_required        = XP.REQUIRED(level_current+1, xp_current)
	xp_required_before = XP.REQUIRED(level_current, xp_current)
	xp_difference      = xp_required - xp_required_before
	xp_collected       = xp_current - xp_required_before
	
	score_progress = (230 / xp_difference) * xp_collected
	
	with open(os.path.join(DIR.TEMPLATES, "score-card_template.svg"), "r") as fobj: template_svg = fobj.read()
	with open(os.path.join(DIR.FONTS, "GillSansMTStd_Medium.base64"), "r") as fobj: font_base64  = fobj.read()
	
	generated_svg = template_svg.format(
		GillSansMTStd_Medium_base64 = font_base64

		, background_color = "transparent"
		, cell_border_color = hex2color(COLOR.DISCORD.CHAT_BG)
		, cell_color = hex2color(COLOR.DISCORD.BLACK)

		, avatar_img = member.display_avatar.url
		, status = member.status.__str__()

		, nickname_color = hex2color(COLOR.HARIBO.LIGHT)
		, username = member.display_name
		
		, score_bar_color = hex2color(COLOR.HARIBO.SUCCESS)
		, score_progress_color = hex2color(COLOR.HARIBO.INFO)
		, score_rating_color = hex2color(COLOR.HARIBO.LIGHT)
		, score_progress_border = 20 + score_progress + 2
		, score_progress = 20 + score_progress

		, current_xp_color = hex2color(COLOR.HARIBO.LIGHT)
		, required_xp_color = hex2color(COLOR.HARIBO.LIGHT)
		, current_xp = formatNum(xp_current)
		, required_xp = xp_required

		, badge_1_color = "#"
		, badge_2_color = "#"
		, badge_3_color = "#"
		, badge_4_color = "#"
		, badge_5_color = "#"
		, badge_more_color = "#"
		, hidden_badges_count = 5

		, ranking_color = hex2color(COLOR.HARIBO.LIGHT)
		, level_color = hex2color(COLOR.HARIBO.LIGHT)
		, rank = 0
		, level = level_current

		, BO = "{"
		, BC = "}"
	)

	score_card_file = lambda ext: os.path.abspath(f"{os.path.join(DIR.TEMP, f'score-card_{member.id}')}.{ext}")
	with open(score_card_file("svg"), "w+") as fobj: fobj.write(generated_svg)
	
	error = svg2png(score_card_file("svg"), score_card_file("png"), 400*4)
	msg = f"svg2png returned error code `{error}`"
	LOG.LOGGER.debug(msg) if error == 0 else LOG.LOGGER.error(msg)

	return score_card_file
