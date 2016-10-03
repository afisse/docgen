#!/opt/Python-2.7/bin/python

import ConfigParser, sys, string, json, argparse, os
import sys, json, random, string, pymongo, time, math
from pymongo import MongoClient
from pymongo.bulk import BulkOperationBuilder

parser = argparse.ArgumentParser (description='Generate random JSON documents')

parser.add_argument ('--input', dest='input', help='Schema file', default='schema.json')
parser.add_argument ('--output', dest='output', help='Document file', default='document.json')
parser.add_argument ('--objects', dest='objects', help='Number of objects to generate', default="100")
parser.add_argument ('--pretty', action='store_true', help='Pretty-print output', default=False)

args = vars(parser.parse_args())

schema = json.load (open (args['input'], "r"))
output = open (args['output'], "w")
number = int(args['objects'])
pretty = args['pretty']

def getRandomInt (maximum):
    return random.randint(0, maximum-1)

def getRandomString (length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

# CACHE THE FILES CONTENT
open_files = {}
def get_random_line_of_file (path):
    if path in open_files:
        content = open_files[path]
    else:
        f = open(path,"r")
        content =  f.read().splitlines()
        f.close()
        open_files[path] = content
    number_line = len(content)
    n = getRandomInt(number_line)
    return content[n]

# HUMAN READABLE BYTES
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

# THOUSANDS SEPARATOR
def intWithCommas(x):
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)

# STRING OF FLOAT
def str_of_float (f,decimal=2):
    a = int(math.floor(f))
    b = int(math.floor((f-a) * (10**decimal)))
    res = intWithCommas (a) + "." + str(b)
    return res

def genValue (field_description):
    type = field_description["type"]
    if type == "integer":
        length = field_description["length"]
        n = getRandomInt (10**length)
        return n
    elif type == "float":
        maximum = field_description["maximum"]
        return random.uniform (0, maximum)
    elif type == "string":
        length = field_description["length"]
        return getRandomString (length)
    elif type == "object":
        schema = field_description["object"]
        return genObject (schema)
    elif type == "array":
        length = field_description["length"]
        element = field_description["element"]
        arr = []
        for i in range (0, length):
            arr.append (genValue (element))
        return arr
    elif type == "word":
        path = field_description["path"]
        line = get_random_line_of_file(path)
        return line
    elif type == "text":
        path = field_description["path"]
        length = field_description["length"]
        text=[]
        for i in range(0, length):
            word = get_random_line_of_file(path)
            text.append(word)
        text = " ".join(text)
        return text

def genObject (schema):
    obj={}
    for key in schema.keys():
        obj[key] = genValue (schema[key])
    return obj

time_before = int(math.floor(time.time() * 1000))

doc = []
for i in range(0,number):
    obj = genObject (schema) 
    doc.append(obj)

time_after = int(math.floor(time.time() * 1000))

time_before2 = int(math.floor(time.time() * 1000))
if pretty:
    d = json.dumps (doc,indent=4)
    output.write(d)
else:
    d = json.dumps (doc)
    output.write(d)
file_size = (len(d)) + 1
output.write("\n")
output.close()
time_after2 = int(math.floor(time.time() * 1000))

s = (time_after - time_before) / float(1000)
round_s = (round (100 * s)) / 100
s2 = (time_after2 - time_before2) / float(1000)
round_s2 = (round (100 * s2)) / 100
speed = math.floor((number / s) * 100) / 100
speed2 = math.floor((file_size / s2) * 100) / 100
print str(intWithCommas(number)) + " documents generated in " + str(s) + " seconds (speed = " + str_of_float(speed) + " doc/s)"
print str(sizeof_fmt(file_size)) + " written on disk in " + str(s2) + " seconds (speed = " + str(sizeof_fmt(speed2)) + "/s)"
