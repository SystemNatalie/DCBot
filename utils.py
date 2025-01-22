import re

def stringToSeconds(string):
    seconds = 0
    regex = r"(?P<days>\d+D)|(?P<hours>\d+H)|(?P<minutes>\d+M)|(?P<seconds>\d+S)"
    matches = re.finditer(regex, string, re.IGNORECASE)
    foundGroup = False
    for match in matches:
        if match.group('days'):
            seconds += int(match.group('days')[:-1]) * 86400
            foundGroup = True
        elif match.group('hours'):
            seconds += int(match.group('hours')[:-1]) * 3600
            foundGroup = True
        elif match.group('minutes'):
            seconds += int(match.group('minutes')[:-1]) * 60
            foundGroup = True
        elif match.group('seconds'):
            print(int(match.group('seconds')[:-1]))
            seconds += int(match.group('seconds')[:-1])
            foundGroup = True
    return (foundGroup, seconds)

def logCall(func): #decorator
    def wrapper(*args, **kwargs):
        print(f"Function called: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]