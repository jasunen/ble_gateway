def _lowercase(obj):
    """
    Make dictionary, list, tuple or string lowercase
    Will traverse thru whole object, i.e. nested dictionaries
    In case of dictionaries, will lowercase both key and value
    """
    if isinstance(obj, dict):
        return {k.lower(): _lowercase(v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
        t = type(obj)
        return t(_lowercase(o) for o in obj)
    elif isinstance(obj, str):
        return obj.lower()
    else:
        return obj
