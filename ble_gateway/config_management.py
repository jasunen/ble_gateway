import copy
import os

import yaml
from benedict import benedict

from ble_gateway import defs

# from ble_gateway import defaults


class Configuration:
    def __init__(self):
        # Configuration has following sections:
        # 'common', 'sources', 'destinations'
        # Inits using default config from defs
        self.__config_sections = [
            defs.C_SEC_COMMON,
            defs.C_SEC_SOURCES,
            defs.C_SEC_DESTINATIONS,
        ]
        self.__config = benedict(keypath_separator=None)
        self.update_config(defs.DEFAULT_CONFIG, False)

    def update_config(self, new_config_d, merge):
        if not new_config_d or not isinstance(new_config_d, dict):
            return

        new_config_d = benedict(**new_config_d, keypath_separator=None)
        new_config_d.standardize()
        if merge:
            self.__config.merge(new_config_d)
        else:
            self.__config.update(new_config_d)

        for section in self.__config_sections:
            defaults = self.__config[section].get("defaults", None)
            if defaults and isinstance(defaults, dict):
                defaults = copy.deepcopy(self.__config[section]["defaults"])
                for k, d in self.__config[section].items():
                    if k != "defaults":
                        new_d = copy.deepcopy(d)
                        self.__config[section][k] = {}
                        self.__config[section][k].update(defaults)
                        self.__config[section][k].update(new_d)

        self.ALLOWED_MACS = self.find_by_key("allowmac", [])
        self.SOURCE_MACS = self.find_by_key(defs.C_SEC_SOURCES, {})
        self.DESTINATIONS = self.find_by_key(defs.C_SEC_DESTINATIONS, {})
        self.SCANMODE = self.find_by_key("scan", False)
        self.DECODE = self.find_by_key("decode", [])
        self.SHOWRAW = self.find_by_key("showraw", False)

    def find_by_key(self, key, default):
        for section in self.__config_sections:
            found = self.__config[section].get(key, None)
            if found is not None:
                return found
        return default

    def load_configfile(self, file):
        # If file exists, reads the content (MUST BE YAML)
        # and updates configuration
        if file == "-":
            return None
        if os.path.isfile(file):
            with open(file) as f:
                print("Reading configfile:", file)
                d = yaml.load(f, Loader=yaml.FullLoader)
                self.update_config(d, True)
            return True
        else:
            print("No configfile found:", file)
            return None

    def write_configfile(self, file):
        _out = {}
        _out.update(self.__config)
        if file == "-":
            print("Running config:")
            print(yaml.dump(_out))
        else:
            print("Writing configfile:", file)
            with open(file, "w") as f:
                yaml.dump(_out, f)

    def print(self):
        self.write_configfile("-")
