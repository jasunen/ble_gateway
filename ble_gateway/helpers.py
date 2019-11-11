import re


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
