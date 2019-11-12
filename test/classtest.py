import sys
from pprint import pprint
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/jani/Projects/ble_gateway/ble_gateway')

import writers


writer = writers.Writer()
dropwriter = writers.DropWriter()
filewriter = writers.FileWriter('defaultfilewriter', {'interval': 10})
writers = writers.Writers()

pprint(vars(writer))
print(writer.type)
pprint(vars(dropwriter))
pprint(vars(filewriter))
pprint(vars(writers))
