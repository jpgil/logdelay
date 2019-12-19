import re

regex_symbols = re.compile(r"\W+")
regex_numbers = re.compile(r"('|:|\,|^| |\t|\.|\()\-*\d+(\-\d\d\-\d\dT\d\d)?")
regex_stopwords = re.compile(r"(\W)(at|to|for|s|with|by|is|the|of)(\W)")

def colorize(l):
    l = regex_symbols.sub( r" ", l )
    l = regex_stopwords.sub( r"\1\3", l )
    l = regex_numbers.sub( r"\1{}", l)
    l = re.sub(' {2,}', ' ', l) 
    return l.strip()

regex_telescope_prefix = re.compile(r"([lw][au]t)[0-9]([a-z]+)")
regex_cmd = re.compile(r"cmd[0-9]+")

def color_paranal(l):
    l = regex_telescope_prefix.sub(r"\1X\2", l)
    l = regex_cmd.sub(r"cmdX", l)
    return colorize(l)

regex_antname = re.compile(r"(\W)(DA|DV|CM|PM)\d{2}")
def color_alma(l):
    l = regex_antname.sub(r"\1ANTxx", l)
    return colorize(l)    