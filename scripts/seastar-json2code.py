#!/usr/bin/env python3

# C++ Code generation utility from Swagger definitions.
# This utility support Both the swagger 1.2 format
#    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/1.2.md
# And the 2.0 format
#    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
# 
# Swagger 2.0 is not only different in its structure (apis have moved, and
# models are now under definitions) It also moved from multiple file structure
# to a single file.
# To keep the multiple file support, each group of APIs will be placed in a single file
# Each group can have a .def.json file with its definitions (What used to be models)
# Because the APIs in definitions are snippets, they are not legal json objects
# and need to be formated as such so that a json parser would work.

import json
import sys
import re
import glob
import argparse
import os
from string import Template

parser = argparse.ArgumentParser(description="""Generate C++ class for json
handling from swagger definition""")

parser.add_argument('--outdir', help='the output directory', default='autogen')
parser.add_argument('-o', help='Output file', default='')
parser.add_argument('-f', help='input file', default='api-java.json')
parser.add_argument('-ns', help="""namespace when set struct will be created
under the namespace""", default='')
parser.add_argument('-jsoninc', help='relative path to the jsaon include',
                    default='json/')
parser.add_argument('-jsonns', help='set the json namespace', default='json')
parser.add_argument('-indir', help="""when set all json file in the given
directory will be parsed, do not use with -f""", default='')
parser.add_argument('-debug', help='debug level 0 -quite,1-error,2-verbose',
                    default='1', type=int)
parser.add_argument('-combined', help='set the name of the combined file',
                    default='autogen/pathautogen.ee')
parser.add_argument('--create-cc', dest='create_cc', action='store_true', default=False,
                    help='Put global variables in a .cc file')
config = parser.parse_args()


valid_vars = {'string': 'sstring', 'int': 'int', 'double': 'double',
             'float': 'float', 'long': 'long', 'boolean': 'bool', 'char': 'char',
             'datetime': 'json::date_time'}

current_file = ''

spacing = "    "
def getitem(d, key, name):
    if key in d:
        return d[key]
    else:
        raise Exception("'" + key + "' not found in " + name)

def fprint(f, *args):
    for arg in args:
        f.write(arg)

def fprintln(f, *args):
    for arg in args:
        f.write(arg)
    f.write('\n')


def open_namespace(f, ns=config.ns):
    fprintln(f, "namespace ", ns , ' {\n')


def close_namespace(f):
    fprintln(f, '}')


def add_include(f, includes):
    for include in includes:
        fprintln(f, '#include ', include)
    fprintln(f, "")

def trace_verbose(*params):
    if config.debug > 1:
        print(''.join(params))


def trace_err(*params):
    if config.debug > 0:
        print(current_file + ':' + ''.join(params))


def valid_type(param):
    if param in valid_vars:
        return valid_vars[param]
    trace_err("Type [", param, "] not defined")
    return param


def type_change(param, member):
    if param == "array":
        if "items" not in member:
            trace_err("array without item declaration in ", param)
            return ""
        item = member["items"]
        if "type" in item:
            t = item["type"]
        elif "$ref" in item:
            t = item["$ref"]
        else:
            trace_err("array items with no type or ref declaration ", param)
            return ""
        return "json_list< " + valid_type(t) + " >"
    return "json_element< " + valid_type(param) + " >"



def print_ind_comment(f, ind, *params):
    fprintln(f, ind, "/**")
    for s in params:
        fprintln(f, ind, " * ", s)
    fprintln(f, ind, " */")

def print_comment(f, *params):
    print_ind_comment(f, spacing, *params)

def print_copyrights(f):
    fprintln(f, "/*")
    fprintln(f, "* Copyright (C) 2014 Cloudius Systems, Ltd.")
    fprintln(f, "*")
    fprintln(f, "* This work is open source software, licensed under the",
           " terms of the")
    fprintln(f, "* BSD license as described in the LICENSE f in the top-",
           "level directory.")
    fprintln(f, "*")
    fprintln(f, "*  This is an Auto-Generated-code  ")
    fprintln(f, "*  Changes you do in this file will be erased on next",
           " code generation")
    fprintln(f, "*/\n")


def print_h_file_headers(f, name):
    print_copyrights(f)
    fprintln(f, "#ifndef __JSON_AUTO_GENERATED_" + name)
    fprintln(f, "#define __JSON_AUTO_GENERATED_" + name + "\n")


def clean_param(param):
    match = re.match(r"^\{\s*([^\}]+)\s*}", param)
    if match:
        return [match.group(1), False]
    return [param, True]


def get_parameter_by_name(obj, name):
    for p in obj["parameters"]:
        if p["name"] == name:
            return p
    trace_err ("No Parameter declaration found for ", name)


def clear_path_ending(path):
    if not path or path[-1] != '/':
        return path
    return path[0:-1]

# check if a parameter is query required.
# It will return true if the required flag is set
# and if it is a query parameter, both swagger 1.2 'paramType' and swagger 2.0 'in' attributes
# are supported
def is_required_query_param(param):
    return "required" in param and param["required"] and ("paramType" in param and param["paramType"] == "query" or "in" in param and param["in"] == "query")

def add_path(f, path, details):
    if "summary" in details:
        print_comment(f, details["summary"])
    param_starts = path.find("{")
    if param_starts >= 0:
        path_reminder = path[param_starts:]
        vals = path.split("/")
        vals.reverse()
        fprintln(f, spacing, 'path_description::add_path("', clear_path_ending(vals.pop()),
           '",', details["method"], ',"', details["nickname"], '")')
        while vals:
            param, is_url = clean_param(vals.pop())
            if is_url:
                fprintln(f, spacing, '  ->pushurl("', param, '")')
            else:
                param_type = get_parameter_by_name(details, param)
                if ("allowMultiple" in param_type and
                    param_type["allowMultiple"] == True):
                    fprintln(f, spacing, '  ->pushparam("', param, '",true)')
                else:
                    fprintln(f, spacing, '  ->pushparam("', param, '")')
    else:
        fprintln(f, spacing, 'path_description::add_path("', clear_path_ending(path), '",',
           details["method"], ',"', details["nickname"], '")')
    if "parameters" in details:
        for param in details["parameters"]:
            if is_required_query_param(param):
                fprintln(f, spacing, '  ->pushmandatory_param("', param["name"], '")')
    fprintln(f, spacing, ";")


def get_base_name(param):
    return os.path.basename(param)


def is_model_valid(name, model):
    if name in valid_vars:
        return ""
    properties = getitem(model[name], "properties", name)
    for var in properties:
        type = getitem(properties[var], "type", name + ":" + var)
        if type == "array":
            items = getitem(properties[var], "items", name + ":" + var)
            try :
                type = getitem(items, "type", name + ":" + var + ":items")
            except Exception as e:
                try:
                    type = getitem(items, "$ref", name + ":" + var + ":items")
                except:
                    raise e
        if type not in valid_vars:
            if type not in model:
                raise Exception("Unknown type '" + type + "' in Model '" + name + "'")
            return type
    valid_vars[name] = name
    return ""

def resolve_model_order(data):
    res = []
    models = set()
    for model_name in data:
        visited = set(model_name)
        missing = is_model_valid(model_name, data)
        resolved = missing == ''
        if not resolved:
            stack = [model_name]
            while not resolved:
                if missing in visited:
                    raise Exception("Cyclic dependency found: " + missing)
                missing_depends = is_model_valid(missing, data)
                if missing_depends == '':
                    if missing not in models:
                        res.append(missing)
                        models.add(missing)
                    resolved = len(stack) == 0
                    if not resolved:
                        missing = stack.pop()
                else:
                    stack.append(missing)
                    missing = missing_depends
        elif model_name not in models:
            res.append(model_name)
            models.add(model_name)
    return res

def create_enum_wrapper(model_name, name, values):
    enum_name = model_name + "_" + name
    res =  "  enum class " + enum_name + " {"
    for enum_entry in values:
        res = res + "  " + enum_entry + ", "
    res = res +  "NUM_ITEMS};\n"
    wrapper = name + "_wrapper"
    res = res + Template("""  struct $wrapper : public json::jsonable  {
        $wrapper() = default;
        virtual std::string to_json() const {
            switch(v) {
        """).substitute({'wrapper' : wrapper})
    for enum_entry in values:
        res = res + "      case " + enum_name + "::" + enum_entry + ": return \"\\\"" + enum_entry + "\\\"\";\n"
    res = res + Template("""      default: return \"\\\"Unknown\\\"\";
        }
     }
    template<class T>
    $wrapper (const T& _v) {
    switch(_v) {
    """).substitute({'wrapper' : wrapper})
    for enum_entry in values:
        res = res + "      case T::" + enum_entry + ": v = " + enum_name + "::" + enum_entry + "; break;\n"
    res = res + Template("""      default: v = $enum_name::NUM_ITEMS;
        }
    }
    template<class T>
    operator T() const {
        switch(v) {
    """).substitute({'enum_name': enum_name})
    for enum_entry in values:
        res = res + "      case " + enum_name + "::" + enum_entry + ": return T::" + enum_entry + ";\n"
    return res + Template("""      default: return T::$value;
          }
        }
        typedef typename std::underlying_type<$enum_name>::type pos_type;
        $wrapper& operator++() {
        v = static_cast<$enum_name>(static_cast<pos_type>(v) + 1);
            return *this;
        }
        $wrapper & operator++(int) {
            return ++(*this);
        }
        bool operator==(const  $wrapper& c) const {
            return v == c.v;
        }
        bool operator!=(const $wrapper& c) const {
            return v != c.v;
        }
        bool operator<=(const $wrapper& c) const {
            return static_cast<pos_type>(v) <= static_cast<pos_type>(c.v);
        }
        static $wrapper begin() {
            return $wrapper ($enum_name::$value);
        }
        static $wrapper end() {
            return $wrapper ($enum_name::NUM_ITEMS);
        }
        static boost::integer_range<$wrapper> all_items() {
            return boost::irange(begin(), end());
        }
        $enum_name v;
    };
    """).substitute({'enum_name': enum_name, 'wrapper' : wrapper, 'value':values[0]})

def to_operation(opr, data):
    data["method"] = opr.upper()
    data["nickname"] = data["operationId"]
    return data

def to_path(path, data):
    data["operations"] = [to_operation(k, data[k]) for k in data]
    data["path"] = path

    return data

def create_h_file(data, hfile_name, api_name, init_method, base_api):
    if config.o != '':
        final_hfile_name = config.o
    else:
        final_hfile_name = config.outdir + "/" + hfile_name
    hfile = open(final_hfile_name, "w")

    if config.create_cc:
        ccfile = open(final_hfile_name.rstrip('.hh') + ".cc", "w")
        add_include(ccfile, ['"{}"'.format(final_hfile_name)])
        open_namespace(ccfile, "seastar")
        open_namespace(ccfile, "httpd")
        open_namespace(ccfile, api_name)
    else:
        ccfile = hfile
    print_h_file_headers(hfile, api_name)
    add_include(hfile, ['<seastar/core/sstring.hh>',
                        '<seastar/json/json_elements.hh>',
                        '<seastar/http/json_path.hh>'])

    add_include(hfile, ['<iostream>', '<boost/range/irange.hpp>'])
    open_namespace(hfile, "seastar")
    open_namespace(hfile, "httpd")
    open_namespace(hfile, api_name)

    if "models" in data:
        models_order = resolve_model_order(data["models"])
        for model_name in models_order:
            model = data["models"][model_name]
            if 'description' in model:
                print_ind_comment(hfile, "", model["description"])
            fprintln(hfile, "struct ", model_name, " : public json::json_base {")
            member_init = ''
            member_assignment = ''
            member_copy = ''
            for member_name in model["properties"]:
                member = model["properties"][member_name]
                if "description" in member:
                    print_comment(hfile, member["description"])
                if "enum" in member:
                    enum_name = model_name + "_" + member_name
                    fprintln(hfile, create_enum_wrapper(model_name, member_name, member["enum"]))
                    fprintln(hfile, "  ", config.jsonns, "::json_element<",
                           member_name, "_wrapper> ",
                           member_name, ";\n")
                else:
                    fprintln(hfile, "  ", config.jsonns, "::",
                           type_change(member["type"], member), " ",
                           member_name, ";\n")
                member_init += "  add(&" + member_name + ',"'
                member_init += member_name + '");\n'
                member_assignment += "  " + member_name + " = " + "e." + member_name + ";\n"
                member_copy += "  e." + member_name + " = " + member_name + ";\n"
            fprintln(hfile, "void register_params() {")
            fprintln(hfile, member_init)
            fprintln(hfile, '}')

            fprintln(hfile, model_name, '() {')
            fprintln(hfile, '  register_params();')
            fprintln(hfile, '}')
            fprintln(hfile, model_name, '(const ' + model_name + ' & e) {')
            fprintln(hfile, '  register_params();')
            fprintln(hfile, member_assignment)
            fprintln(hfile, '}')
            fprintln(hfile, "template<class T>")
            fprintln(hfile, model_name, "& operator=(const ", "T& e) {")
            fprintln(hfile, member_assignment)
            fprintln(hfile, "  return *this;")
            fprintln(hfile, "}")
            fprintln(hfile, model_name, "& operator=(const ", model_name, "& e) {")
            fprintln(hfile, member_assignment)
            fprintln(hfile, "  return *this;")
            fprintln(hfile, "}")
            fprintln(hfile, "template<class T>")
            fprintln(hfile, model_name, "& update(T& e) {")
            fprintln(hfile, member_copy)
            fprintln(hfile, "  return *this;")
            fprintln(hfile, "}")
            fprintln(hfile, "};\n\n")

 #   print_ind_comment(hfile, "", "Initialize the path")
#    fprintln(hfile, init_method + "(const std::string& description);")
    fprintln(hfile, 'static const sstring name = "', base_api, '";')
    for item in data["apis"]:
        path = item["path"]
        if "operations" in item:
            for oper in item["operations"]:
                if "summary" in oper:
                    print_comment(hfile, oper["summary"])

                param_starts = path.find("{")
                base_url = path
                vals = []
                if param_starts >= 0:
                    vals = path[param_starts:].split("/")
                    vals.reverse()
                    base_url = path[:param_starts]

                varname = getitem(oper, "nickname", oper)
                if config.create_cc:
                    fprintln(hfile, 'extern const path_description ', varname, ';')
                    maybe_static = ''
                else:
                    maybe_static = 'static '
                fprintln(ccfile, maybe_static, 'const path_description ', varname, '("', clear_path_ending(base_url),
                       '",', oper["method"], ',"', oper["nickname"], '",')
                fprint(ccfile, '{')
                first = True
                while vals:
                    path_param, is_url = clean_param(vals.pop())
                    if path_param == "":
                        continue
                    if first == True:
                        first = False
                    else:
                        fprint(ccfile, "\n,")
                    if is_url:
                        fprint(ccfile, '{', '"/', path_param , '", path_description::url_component_type::FIXED_STRING', '}')
                    else:
                        path_param_type = get_parameter_by_name(oper, path_param)
                        if ("allowMultiple" in path_param_type and
                            path_param_type["allowMultiple"] == True):
                            fprint(ccfile, '{', '"', path_param , '", path_description::url_component_type::PARAM_UNTIL_END_OF_PATH', '}')
                        else:
                            fprint(ccfile, '{', '"', path_param , '", path_description::url_component_type::PARAM', '}')
                fprint(ccfile, '}')
                fprint(ccfile, ',{')
                first = True
                enum_definitions = ""
                if "enum" in oper:
                    enum_definitions = ("namespace ns_" + oper["nickname"] + " {\n" +
                                       create_enum_wrapper(oper["nickname"], "return_type", oper["enum"]) +
                                       "}\n")
                funcs = ""
                if "parameters" in oper:
                    for param in oper["parameters"]:
                        if is_required_query_param(param):
                            if first == True:
                                first = False
                            else:
                                fprint(ccfile, "\n,")
                            fprint(ccfile, '"', param["name"], '"')
                        if "enum" in param:
                            enum_definitions = enum_definitions + 'namespace ns_' + oper["nickname"] + '{\n'
                            enm = param["name"]
                            enum_definitions = enum_definitions + 'enum class ' + enm + ' {'
                            for val in param["enum"]:
                                enum_definitions = enum_definitions + val + ", "
                            enum_definitions = enum_definitions + 'NUM_ITEMS};\n'
                            enum_definitions = enum_definitions + enm + ' str2' + enm + '(const sstring& str);'

                            funcs = funcs + enm + ' str2' + enm + '(const sstring& str) {\n'
                            funcs = funcs + '  static const sstring arr[] = {"' + '","'.join(param["enum"]) + '"};\n'
                            funcs = funcs + '  int i;\n'
                            funcs = funcs + '  for (i=0; i < ' + str(len(param["enum"])) + '; i++) {\n'
                            funcs = funcs + '    if (arr[i] == str) {return (' + enm + ')i;}\n}\n'
                            funcs = funcs + '  return (' + enm + ')i;\n'
                            funcs = funcs + '}\n'

                            enum_definitions = enum_definitions + '}\n'

                fprintln(ccfile, '});')
                fprintln(hfile, enum_definitions)
                open_namespace(ccfile, 'ns_' + oper["nickname"])
                fprintln(ccfile, funcs)
                close_namespace(ccfile)

    close_namespace(hfile)
    close_namespace(hfile)
    close_namespace(hfile)
    if config.create_cc:
        close_namespace(ccfile)
        close_namespace(ccfile)
        close_namespace(ccfile)

    hfile.write("#endif //__JSON_AUTO_GENERATED_HEADERS\n")
    hfile.close()

def remove_leading_comma(data):
    return re.sub(r'^\s*,', '', data)

def format_as_json_object(data):
    return "{" + remove_leading_comma(data) + "}"

def check_for_models(data, param):
    model_name = param.replace(".json", ".def.json")
    if not os.path.isfile(model_name):
        return 
    try:
        with open(model_name) as myfile:
            json_data = myfile.read()
            def_data = json.loads(format_as_json_object(json_data))
            data["models"] = def_data
    except Exception as e:
        type, value, tb = sys.exc_info()
        print("Bad formatted JSON definition file '" + model_name + "' error ", value.message)
        sys.exit(-1)

def set_apis(data):
    return {"apis": [to_path(p, data[p]) for p in data]}

def parse_file(param, combined):
    global current_file
    trace_verbose("parsing ", param, " file")
    with open(param) as myfile:
        json_data = myfile.read()
    try:
        data = json.loads(json_data)
    except Exception as e:
        try:
            # the passed data is not a valid json, so maybe its a swagger 2.0
            # snippet, format it as json and try again
            # set_apis and check_for_models will create an object with a similiar format
            # to a swagger 1.2 so the code generation would work
            data = set_apis(json.loads(format_as_json_object(json_data)))
            check_for_models(data, param)
        except:
            # The problem is with the file,
            # just report the error and exit.
            type, value, tb = sys.exc_info()
            print("Bad formatted JSON file '" + param + "' error ", value.message)
            sys.exit(-1)
    try:
        base_file_name = get_base_name(param)
        current_file = base_file_name
        hfile_name = base_file_name + ".hh"
        api_name = base_file_name.replace('.', '_')
        base_api = base_file_name.replace('.json', '')
        init_method = "void " + api_name + "_init_path"
        trace_verbose("creating ", hfile_name)
        if (combined):
            fprintln(combined, '#include "', base_file_name, ".cc", '"')
        create_h_file(data, hfile_name, api_name, init_method, base_api)
    except:
        type, value, tb = sys.exc_info()
        print("Error while parsing JSON file '" + param + "' error ", value.message)
        sys.exit(-1)

if "indir" in config and config.indir != '':
    combined = open(config.combined, "w")
    for f in glob.glob(os.path.join(config.indir, "*.json")):
        parse_file(f, combined)
else:
    parse_file(config.f, None)
