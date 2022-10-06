
# libs
import os, logging, random
from math import sqrt, floor

#---------#
# globals #
#---------#

class TOKEN:
	DISCORD  = open(os.path.abspath(r"../discord.token"), "r").readlines()[0].strip()
	OWNER_ID = int(open(os.path.abspath(r"../discord.owner"), "r").readlines()[0].strip())

class COLOR:

	class HARIBO:
		# HARIBO color palette
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
		# HARIBO corporate colors
		PRIMARY   = 0x3390B4
		SECONDARY = GRAY
		SUCCESS   = GREEN
		INFO      = CYAN
		WARNING   = YELLOW
		DANGER    = RED
		LIGHT     = 0xF8F9FA
		DARK      = GRAY_DARK
	
	class DISCORD:
		# DISCORD color palette
		BLURPLE = 0x5865F2
		GREEN   = 0x57f287
		YELLOW  = 0xFEE75C
		RED     = 0xED4245
		FUCHSIA = 0xEB459E
		WHITE   = 0xFFFFFF
		BLACK   = 0x23272A
		# DISCORD-UI colors
		CHAT_BG = 0x32353B

class CONFIG:
	PREFIX       = "/"
	EPHEMERAL    = False

class DIR:
	MAIN      = ".."
	TEMP      = os.path.abspath(f"{MAIN}/tmp")
	DATA      = os.path.abspath(f"{MAIN}/data")
	APPS      = os.path.abspath(f"{MAIN}/apps")
	ASSETS    = os.path.abspath(f"{MAIN}/assets")
	FONTS     = os.path.abspath(f"{ASSETS}/fonts")
	IMGAGES   = os.path.abspath(f"{ASSETS}/img")
	TEMPLATES = os.path.abspath(f"{ASSETS}/templates")

class XP:
	MULTIPLIER = 0.5
	COOLDOWN   = 30
	DEFAULT    = 100
	RANGE      = {"min": 15, "max": 25}
	REQUIRED   = lambda lvl, xp: 5*(lvl**2) + (50*lvl) + XP.DEFAULT
	LEVEL      = lambda xp: floor(0.2 * (sqrt(5) * sqrt(xp+25) - 25))
	GENERATE   = lambda t0, t1: (random.randint(XP.RANGE["min"], XP.RANGE["max"]) * XP.MULTIPLIER) if (t1 - t0) >= XP.COOLDOWN else XP.MULTIPLIER

class LOG:
	FMT      = "%(asctime)s | %(levelname)8s | %(message)s"
	DATE_FMT = "%Y-%m-%d %H:%M:%S"
	DIR      = os.path.abspath("../log")
	FILE     = "log.dat"
	PATH     = os.path.abspath(os.path.join(DIR, FILE))
	LEVEL    = logging.DEBUG
	LOGGER   = None

class BOTINFO:
	ID          = 1024235031037759500
	NAME        = "HARIBOT"
	DESCRIPTION = 'A discord bot specialized for the **Dr. Hans Riegel - Stiftung** community discord server.'
	INVITE      = f"https://discord.com/oauth2/authorize?client_id={ID}&permissions=8&scope=bot"
	REPOSITORY  = "FabianBartl/HARIBOT"
	CREATOR     = "Fabian Bartl"
