def upgrade_type_case(case):
    name, args = case
    # print args
    args = ["(%s)"%new_type_info(arg) for arg in args] 
    return [name, args]

def upgrade_type(type):
    type["cases"] = map(upgrade_type_case, type["cases"])
    return type


def upgrade_app_args(arg, out=True):
    if arg['tag'] == 'var' or arg['tag'] == 'type':
        return arg["name"]
    if arg['tag'] == 'record': return upgrade_record(arg)
    if arg['tag'] == 'lambda':
        if not out: 
            return new_type_info(arg)
        else:
            return "(%s)"%new_type_info(arg)
    else: return "(%s)"%upgrade_app(arg)

def upgrade_app(app):

    name = app["func"]["name"]
    if "Tuple" in name:
        if "0" in name: return " "
        return ", ".join(map(upgrade_app_args, app["args"]))
    else:
        return "%s %s"%(name, " ".join(map(upgrade_app_args, app["args"])))

def field(field):
    return "%s : %s"%field

def upgrade_record(record):

    new_record = [(name, new_type_info(val)) for (name, val) in record["fields"]]
    
    if len(new_record) == 0: return "{ }"

    return " { %s"%field(new_record[0]) +", "+",".join(map(field, new_record[1:]))+" }"

def new_type_info(type):
    
    if type["tag"] == "type" or type["tag"] == "var":
        return type["name"]

    if type["tag"] == "record":
        return upgrade_record(type)

    if type["tag"] == "app":
        return upgrade_app(type)
    
    if type["tag"] == "lambda":
        return "%s -> %s"%(upgrade_app_args(type["in"]), upgrade_app_args(type["out"], False))

    print "error", type
    return ""

def upgrade_type_info(value):
    value["type"] = new_type_info(value["type"])
    return value

def upgrade_json(json):

    json["types"] = map(upgrade_type, json["types"])

    json["values"] = map(upgrade_type_info, json["values"])
    json["aliases"] = map(upgrade_type_info, json["aliases"])

    return json

