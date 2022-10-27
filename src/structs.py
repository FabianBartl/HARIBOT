
# ================= LIBRARIES ========================================================================================

# ------- other libs ---------------------------------------------------------

import os, logging, random, json
from math import sqrt, floor

# ================= OBJECTS, FUNCTION COLLECTIONS, DATA CLASSES ======================================================

# ------- color object -------------------------------------------------------

class COLOR:
	def __init__(self, r: int, g: int, b: int, a: int=None) -> object:
		self.r, self.g, self.b = r, g, b
		self.has_a = a is not None
		self.a = a if self.has_a else 0xFF
	
	def __int__(self) -> int: return int(f"{self:#}"[1:], 16)

	def __format__(self, __format_spec: str) -> str:
		with_a = ((len(__format_spec) >= 2 and __format_spec[1] == "a") or self.has_a) and (len(__format_spec) >= 2 and __format_spec[1] != "n")
		if   __format_spec[0] == "#": return f"#{self.fitHex(self.r)}{self.fitHex(self.g)}{self.fitHex(self.b)}{self.fitHex(self.a) if with_a else ''}"
		elif __format_spec[0] == "d": return f"rgb{'a' if with_a else ''}({self.r}, {self.g}, {self.b}{f', {self.a}' if with_a else ''})"
		else: raise ValueError("Invalid format specifier")

	def fitHex(self, val: int) -> str: return f"{hex(val)[2:]:0>2}"

# ------- colors ---------------------------------------------------------

class COLOR(COLOR):
	def __init__(self, *args):
		super().__init__(*args)
	
	class HARIBO:
		# HARIBO color palette
		BLUE      = COLOR(0x00, 0x7B, 0xFF)
		INDIGO    = COLOR(0x66, 0x10, 0xF2)
		PURPLE    = COLOR(0x6F, 0x42, 0xC1)
		PINK      = COLOR(0xE8, 0x3E, 0x8C)
		RED       = COLOR(0xE2, 0x00, 0x1A)
		ORANGE    = COLOR(0xFD, 0x7E, 0x14)
		YELLOW    = COLOR(0xFF, 0xC1, 0x07)
		GREEN     = COLOR(0x28, 0xA7, 0x45)
		TEAL      = COLOR(0x20, 0xC9, 0x97)
		CYAN      = COLOR(0x17, 0xA2, 0xB8)
		WHITE     = COLOR(0xFF, 0xFF, 0xFF)
		GRAY      = COLOR(0x6C, 0x75, 0x7D)
		GRAY_DARK = COLOR(0x34, 0x3A, 0x40)
		# HARIBO corporate colors
		PRIMARY   = COLOR(0x33, 0x90, 0xB4)
		SECONDARY = GRAY
		SUCCESS   = GREEN
		INFO      = CYAN
		WARNING   = YELLOW
		DANGER    = RED
		LIGHT     = COLOR(0xF8, 0xF9, 0xFA)
		DARK      = GRAY_DARK

	class DISCORD:
		# DISCORD color palette
		BLURPLE = COLOR(0x58, 0x65, 0xF2)
		GREEN   = COLOR(0x57, 0xf2, 0x87)
		YELLOW  = COLOR(0xFE, 0xE7, 0x5C)
		RED     = COLOR(0xED, 0x42, 0x45)
		FUCHSIA = COLOR(0xEB, 0x45, 0x9E)
		WHITE   = COLOR(0xFF, 0xFF, 0xFF)
		BLACK   = COLOR(0x23, 0x27, 0x2A)
		# DISCORD-UI colors
		CHAT_BG = COLOR(0x32, 0x35, 0x3B)

# ------- XP functions, config -----------------------------------------------

class XP:
	RANGE            = {"min": 15, "max": 25}
	RANGE_MULTIPLIER = 0.5
	DEFAULT          = 100
	REQUIRED         = lambda lvl, xp: 5*(lvl**2) + (50*lvl) + XP.DEFAULT
	COOLDOWN         = 30
	COOLDOWN_ELAPSED = lambda t0, t1: (t1 - t0) >= XP.COOLDOWN
	LEVEL            = lambda xp: floor(0.2 * (sqrt(5) * sqrt(xp+25) - 25))
	GENERATE         = lambda t0, t1: (random.randint(XP.RANGE["min"], XP.RANGE["max"]) * XP.RANGE_MULTIPLIER) if XP.COOLDOWN_ELAPSED(t0, t1) else XP.RANGE_MULTIPLIER

# ------- logger function, config -----------------------------------------------

class LOG:
	FMT      = "%(asctime)s | %(levelname)8s | %(message)s"
	DATE_FMT = "%Y-%m-%d %H:%M:%S"
	DIR      = os.path.abspath("../log")
	FILE     = "log.dat"
	PATH     = os.path.abspath(os.path.join(DIR, FILE))
	LEVEL    = logging.DEBUG
	LOGGER   = None

# ------- directories --------------------------------------------------------

class DIR:
	MAIN      = ".."
	TEMP      = os.path.abspath(f"{MAIN}/tmp")
	DATA      = os.path.abspath(f"{MAIN}/data")
	PGP       = os.path.abspath(f"{DATA}/pgp")
	APPS      = os.path.abspath(f"{MAIN}/apps")
	ASSETS    = os.path.abspath(f"{MAIN}/assets")
	CONFIGS   = os.path.abspath(f"{ASSETS}/configs")
	FONTS     = os.path.abspath(f"{ASSETS}/fonts")
	IMGAGES   = os.path.abspath(f"{ASSETS}/imgs")
	TEMPLATES = os.path.abspath(f"{ASSETS}/templates")

# ------- secret values ------------------------------------------------------

tmpFile = os.path.abspath(os.path.join(DIR.MAIN, "tokens.json"))
with open(tmpFile, "r") as fobj: tmpJSON = json.load(fobj)

class TOKEN:
	DISCORD = tmpJSON.get("discord")
	TEAMUP  = tmpJSON.get("teamup")

del tmpFile, tmpJSON

# ------- basic config, info -------------------------------------------------

class CONFIG:
	PREFIX    = "!"
	EPHEMERAL = False

class INFO:
	class BOT:
		ID          = 1024235031037759500
		NAME        = "HARIBOT"
		DESCRIPTION = 'A discord bot specialized for the **Dr. Hans Riegel - Stiftung** community discord server.'
		INVITE      = f"https://discord.com/oauth2/authorize?client_id={ID}&permissions=8&scope=bot"
		REPOSITORY  = "FabianBartl/HARIBOT"
		CREATOR     = "Fabian Bartl"
		OWNER       = 386249332711620608

	class SERVER:
		INVITE = "GVs3hmCmmJ"
		TEAMUP = "ks7yff4qzz9avhm6aa"
