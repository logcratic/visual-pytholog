import unicodedata

from inspect import getframeinfo

facts_file = r''
constant_facts_file = r''
wizard_facts_file = r''
facts_location_file = r''

fact_files = [facts_file, constant_facts_file, wizard_facts_file, facts_location_file]

globals_file = r"globals.ini"

def get_global(variable):
    global_dict = eval(open(globals_file).read())
    return global_dict[variable]

def set_global(variable, string):
    try:
        global_dict = eval(open(globals_file).read())
    except:
        global_dict = dict()
    global_dict[variable] = string
    open(globals_file,"w").write(str(global_dict))

def get_context_above_frame(frame):
    frame.f_lineno -= 1
    return getframeinfo(frame)[3][0].strip()


def clear_facts():
    for file in fact_files:
        try:
            open(file, 'w').close()
        except:
            with open(file,"a+") as f: pass


def write_fact(predicate, terms, location, previous_context=None):
    save_fact_to_file(predicate, terms, location, facts_file, previous_context)


def write_constant_fact(predicate, terms, location, previous_context=None):
    save_fact_to_file(predicate, terms, location, constant_facts_file, previous_context)


def write_wizard_fact(predicate, terms, location, previous_context=None):
    save_fact_to_file(predicate, terms, location, wizard_facts_file, previous_context)


def save_fact_to_file(predicate, terms, location, file, previous_context=None):
    file_object = open(file, 'a',encoding="utf8")
    fact = predicate + "(" + clean_terms(terms) + ")."
    try:
        file_object.write(fact + "\n")
    except:
        print("Could not write fact!")
    file_object.close()
    save_fact_location(fact, location, previous_context)


def clean_terms(terms):
    string = ''
    for term in terms:
        if str(term)[0].isdigit() or str(term)[0] == "_" or (str(term).startswith(".") and str(term)[1].isdigit()):
            term = "d" + str(term)
        string += unicodedata.normalize("NFKC",str(term).strip().replace("<","smaller").replace(">","greater").replace("=","equal").replace("*","_").replace("+","_").replace(",", "").replace(" ", "_").replace("-", "_").replace(".", "_").replace("/","").replace("\\", "").replace("<<divide>>", "__").replace(":", "").replace("\n", "").replace("\t", "").replace("(","").replace(")","").replace("%","percent").replace("^","power").replace("\xc2\xb5","micro").lower())
        string += ","
    return string[:-1]

def save_fact_location(fact, location, previous_context=None):
    file_object = open(facts_location_file, 'a',encoding="utf8")
    path = location[0].split("trilodocs_backend")[1]
    lineno = str(location[1])
    function = str(location[2])
    context = str([code for code in str(location[3]).split(";") if "location" not in code and "fact" not in code])
    if not previous_context:
        file_object.write(fact + "\t" + path + "\t" + lineno + "\t" + function + "\t" + context + "\t" + "" + "\n")
    else:
        file_object.write(
            fact + "\t" + path + "\t" + lineno + "\t" + function + "\t" + context + "\t" + previous_context + "\n")
    file_object.close()



