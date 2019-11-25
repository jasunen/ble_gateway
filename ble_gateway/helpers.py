import re
import time


class StopWatch:
    def __init__(self, timeout=0):
        self.TIMER_SECS = 0.0  # Cumulative seconds
        self.TIMER_COUNT = 0  # Cumulative counter
        self.__start_t = self.now()
        self.__timeout = timeout
        self.MAX_SPLIT = 0.0

    def start(self):
        self.__start_t = self.now()
        return self.__start_t

    def split(self):
        split_t = self.now()
        laptime = split_t - self.__start_t
        self.MAX_SPLIT = max(self.MAX_SPLIT, laptime)
        self.TIMER_SECS += laptime
        self.TIMER_COUNT += 1
        return split_t

    def set_timeout(self, tout):
        self.__timeout = tout

    def get_timeout(self):
        return self.__timeout

    def is_timeout(self):
        if self.__timeout:
            return self.now() - self.__start_t > self.__timeout
        else:
            return False

    def now(self):
        return time.time()

    def get_count(self):
        return self.TIMER_COUNT

    def get_average(self):
        if self.TIMER_COUNT > 0:
            return self.TIMER_SECS / self.TIMER_COUNT
        else:
            return 0

    def reset(self):
        self.__init__(self.__timeout)


def uptime_str(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    d = [("s", seconds), ("m", minutes), ("h", hours), ("d", days), ("w", weeks)]
    result = []
    for (s, v) in d:
        if v:
            result.append("{}{}".format(v, s))
    result.reverse()
    return ":".join(result)


# helper func to verify and format macaddress
def check_and_format_mac(val):
    if not isinstance(val, str):
        return False
    try:
        val = val.lower()
        val = val.replace("_", ":")
        val = val.replace("-", ":")
        if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", val):
            return val
    except Exception as e:
        print("Error: " + str(e))
    return False


def _lowercase_all(obj):
    """
    Make dictionary, list, tuple or string lowercase
    Will traverse thru whole object, i.e. nested dictionaries
    In case of dictionaries, will lowercase both key and value
    """
    if isinstance(obj, dict):
        return {k.lower(): _lowercase_all(v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
        t = type(obj)
        return t(_lowercase_all(o) for o in obj)
    elif isinstance(obj, str):
        return obj.lower()
    else:
        return obj


def _lowercase_keys(obj):
    """
    Make dictionary keys (and ONLY dictionary keys) lowercase
    Will traverse thru whole object, i.e. nested dictionaries
    """
    if isinstance(obj, dict):
        return {k.lower(): _lowercase_keys(v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
        t = type(obj)
        return t(_lowercase_keys(o) for o in obj)
    elif isinstance(obj, str):
        return obj
    else:
        return obj
