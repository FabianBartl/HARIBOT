
import os, logging

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
	PREFIX    = "/"
	DATA_DIR  = os.path.abspath("../data")
	EPHEMERAL = True
	LOG_DIR   = os.path.abspath("../log")
	LOG_FILE  = os.path.abspath(f"{LOG_DIR}/log.dat")
	LOG_LEVEL = logging.DEBUG

class DATABASE:
	DB_FILE    = "../data/data.db"
	CONNECTION = None
	CURSOR     = None

class BOTINFO:
	ID          = 1024235031037759500
	NAME        = "HARIBOT"
	DESCRIPTION = 'A discord bot specialized for the "Dr. Hans Riegel - Stiftung" community discord server.'
	INVITE      = f"https://discord.com/oauth2/authorize?client_id={ID}&permissions=8&scope=bot"
	REPOSITORY  = "FabianBartl/HARIBOT"
	CREATOR     = "Fabian Bartl"
