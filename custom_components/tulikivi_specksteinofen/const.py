"""Constants for the Tulikivi Specksteinofen integration."""

DOMAIN = "tulikivi_specksteinofen"

CONF_FLUE_SENSOR = "flue_sensor"
CONF_STONE_SENSOR = "stone_sensor"
CONF_ROOM_SENSOR = "room_sensor"
CONF_MASS = "mass"
CONF_ROOM_TEMP = "room_temp"
CONF_MAX_TEMP = "max_temp"
CONF_AUTO_LEARN = "auto_learn"

DEFAULT_NAME = "Tulikivi Specksteinofen"
DEFAULT_MASS = 1000
DEFAULT_ROOM_TEMP = 20.0
DEFAULT_MAX_TEMP = 70.0
DEFAULT_AUTO_LEARN = True

# Spezifische Wärmekapazität von Speckstein: ca. 0.98 kJ/(kg*K) = 0.0002722 kWh/(kg*K)
SPECIFIC_HEAT_CAPACITY = 0.0002722
