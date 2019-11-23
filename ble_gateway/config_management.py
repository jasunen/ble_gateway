import copy
import os
import sys

import ruamel.yaml
from benedict import benedict

from ble_gateway import defs, helpers

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

    def get_config_dict(self):
        return self.__config

    def update_attributes(self):
        self.ALLOWED_MACS = self.find_by_key("allowmac", [])
        self.MODE = self.find_by_key("mode", defs.GWMODE)
        self.DECODE = self.find_by_key("decode", [])
        self.SHOWRAW = self.find_by_key("showraw", False)
        self.SIMULATOR = self.find_by_key("simulator", 0)
        self.DEVICE = self.find_by_key("device", 0)
        self.MAX_MESGS = self.find_by_key("max_mesgs", 0)

        if self.SIMULATOR:
            self.SIMUMACS = list(self.SOURCES.keys())
            self.SIMUMACS.remove("*")
            self.SIMUMACS.remove("defaults")

        if self.MODE == defs.SCANMODE:
            self.SOURCES = {"*": {"destinations": ["SCAN"], "decoders": self.DECODE}}
            self.DESTINATIONS = {"SCAN": {"type": "SCAN"}}
        else:
            self.SOURCES = self.__config.get(defs.C_SEC_SOURCES, {})
            self.DESTINATIONS = self.__config.get(defs.C_SEC_DESTINATIONS, {})
            self.DESTINATIONS["DROP"] = {"type": "DROP"}
            self.DESTINATIONS["SCAN"] = {"type": "SCAN"}

    def update_config(self, new_config_d, merge):
        if not new_config_d or not isinstance(new_config_d, dict):
            return

        #
        # benedict.standardize messes up mac addresses !!!
        # new_config_d = benedict(new_config_d, keypath_separator=None)
        # new_config_d.standardize()
        # need to use self-made function
        new_config_d = helpers._lowercase_keys(new_config_d)
        if merge:
            self.__config.merge(new_config_d)
        else:
            self.__config.update(new_config_d)

        # Verifay that configuration includes only known sections
        # Remove invalid sections
        for section in list(self.__config.keys()):
            if section not in self.__config_sections:
                del self.__config[section]
                print("Removing uknown section '{}' in configuration.".format(section))

        # Apply defaults to source and destination definitions
        for section in self.__config_sections:
            defaults = self.__config[section].pop("defaults", None)
            if defaults and isinstance(defaults, dict):
                for k, d in self.__config[section].items():
                    self.__config[section][k] = {}
                    self.__config[section][k].update(defaults)
                    if isinstance(d, dict):
                        new_d = {}
                        new_d = copy.deepcopy(d)
                        self.__config[section][k].update(new_d)
                self.__config[section]["defaults"] = {}
                self.__config[section]["defaults"].update(defaults)
        #
        # NOTE !!!!!!!!!!!!!!!!!
        # beendict().standardize() re-formats mac addresses by
        # replacing ':' with '_'
        # Need to parse macs (keys) in SOURCE_MACS and rename if wrong format
        #
        for mac in list(self.__config[defs.C_SEC_SOURCES].keys()):
            new_mac = helpers.check_and_format_mac(mac)
            if new_mac:
                self.__config[defs.C_SEC_SOURCES][new_mac] = self.__config[
                    defs.C_SEC_SOURCES
                ].pop(mac)
        self.update_attributes()

    def find_by_key(self, key, default=None):
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
                yaml = ruamel.yaml.YAML()
                d = yaml.load(f)
            return d
        else:
            print("No configfile found:", file)
            return None

    def write_configfile(self, file, config={}):
        if not file:
            return
        if not config:
            config = self.__config
        _out = {}
        _out.update(self.__config)
        yaml = ruamel.yaml.YAML()
        if file == "-":
            print("Configuration as YAML:")
            yaml.dump(_out, sys.stdout)
        else:
            print("Writing to configfile:", file)
            with open(file, "w") as f:
                yaml.dump(_out, f)

    def print(self):
        self.write_configfile("-")
