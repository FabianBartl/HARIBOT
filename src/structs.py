
import os, logging
from commands import *

class TOKEN:
	DISCORD = open(os.path.abspath(r"../discord.token"), "r").readlines()[0].strip()

class COLOR:
	BLUE      = 0x007BFF
	INDIGO    = 0x6610F2
	PURPLE    = 0x6F42C1
	PINK      = 0xE83E8C
	RED       = 0xE2001A
	ORANGE    = 0xFD7E14
	YELLOW    = 0xFFC107
	GREEN     = 0x28A745
	TEAL      = 0x20C997
	CYAN      = 0x17A2B8
	WHITE     = 0xFFFFFF
	GRAY      = 0x6C757D
	GRAY_DARK = 0x343A40
	PRIMARY   = 0x3390B4
	SECONDARY = 0x6C757D
	SUCCESS   = 0x28A745
	INFO      = 0x17A2B8
	WARNING   = 0xFFC107
	DANGER    = 0xE2001A
	LIGHT     = 0xF8F9FA
	DARK      = 0x343A40

class CONFIG:
	INVITE    = "https://discord.com/oauth2/authorize?client_id=1024235031037759500&permissions=8&scope=bot"
	DATA_DIR  = "../data"
	LOG_FILE  = "../log.dat"
	LOG_LEVEL = logging.DEBUG

class COMMAND:
	PREFIX    = "!"
	SEPARATOR = " "
	DICT      = {
		"unknowCommand": lambda args: EXECUTE.unknownCommand(*args)
		, "ping":        lambda args: EXECUTE.ping          (*args)
		, "userInfo":    lambda args: EXECUTE.userInfo      (*args)
		, "guildInfo":   lambda args: EXECUTE.guildInfo     (*args)
	}
