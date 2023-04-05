import re

def split(name):
    p = re.sub(r"([-_\s]+)", r" ",name)
    return re.sub( r"([A-Z])", r" \1",p).lower().split()


#dieser_satz_ist_snake_case_geschrieben
def snake_case(name):
    p = split(name)
    return "_".join(p)