import re

regex_symbols = re.compile(r"\W+")
regex_numbers = re.compile(r"('|:|\,|^| |\t|\.|\()\-*\d+(\-\d\d\-\d\dT\d\d)?")
regex_stopwords = re.compile(r"(\W)(at|to|for|s|with|by|is|the|of)(\W)")
regex_UTCdate = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{0,3})?")

def colorize(l):
    l = regex_UTCdate.sub( r"_date_", l )
    l = regex_symbols.sub( r" ", l )
    l = regex_stopwords.sub( r"\1\3", l )
    l = regex_numbers.sub( r"\1{}", l)
    l = re.sub(' {2,}', ' ', l) 
    return l.strip().lower()


# Paranal color
regex_telescope_prefix = re.compile(r"([lw][au]t)[0-9]([a-z]+)")
regex_cmd = re.compile(r"cmd[0-9]+")
regex_fits = re.compile(r"([A-Za-z\d_])+\.fits")
regex_procname = re.compile(r"([a-z]+)_\d{4,}")
regex_obs_param = re.compile(r"((OBS|SEQ|INS)\.[A-Z:\._]+ )[A-Za-z\d_]+")

def color_paranal(l):
    l = regex_obs_param.sub(r"\1 000", l)
    l = regex_procname.sub(r"\1_X", l)
    l = regex_fits.sub(r"0_fits", l)
    l = regex_telescope_prefix.sub(r"\1X\2", l)
    l = regex_cmd.sub(r"cmdX", l)
    return colorize(l)


# ALMA Color
regex_antname = re.compile(r"(\W)(DA|DV|CM|PM)\d{2}")
def color_alma(l):
    if type(l) != type(""):
        l = " "
    l = regex_antname.sub(r"\1ANTxx", l)
    return colorize(l)    