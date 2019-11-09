import os

import yaml
from benedict import benedict

from ble_gateway import defs

# from ble_gateway import defaults


class Configuration:
    def __init__(self, default_config):
        # Configuration has following sections:
        # 'common', 'sources', 'destinations'
        self.__config_sections = {
            defs.C_SEC_COMMON: benedict(keypath_separator=None),
            defs.C_SEC_SOURCES: benedict(keypath_separator=None),
            defs.C_SEC_DESTINATIONS: benedict(keypath_separator=None),
        }
        self.update_all(default_config)

    def update_all(self, d):
        if d:
            d = benedict(d, keypath_separator=None)
            d.standardize()
            for section in self.__config_sections:
                if section in d:
                    self.update_section(section, d)

    def update_section(self, s, d):
        if d and s:
            d = benedict(d, keypath_separator=None)
            d.standardize()
            self.__config_sections[s].update(d)

    def apply_defaults_to_sources_and_destinations(self):
        for section in self.__config_sections.values():
            defaults = section.get("_defaults_", {})
            if defaults:
                for k, d in section.items():
                    section[k] = {**defaults, **d}

    def load_configfile(self, file):
        # If file exists, reads the content (MUST BE YAML)
        # and updates configuration
        if file == "-":
            return None
        if os.path.isfile(file):
            with open(file) as f:
                print("Reading configfile:", file)
                self.update_all(yaml.load(f, Loader=yaml.FullLoader))
            return True
        else:
            print("No configfile found:", file)
            return None

    def write_configfile(self, file):
        print("Writing configfile:", file)
        _out = {}
        for section in self.__config_sections:
            _out.update(self.__config_sections.get_dict(section))
        if file == "-":
            print(yaml.dump(_out))
        else:
            with open(file, "w") as f:
                yaml.dump(_out, f)

    def find_by_key(self, key, default):
        for section in self.__config_sections.values():
            found = section.get(key, None)
            if found:
                return found
        return default
