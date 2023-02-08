#!/usr/bin/python3

from os.path import exists

name_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
op_chars = '+-*/^()[]{}%!$'
num_chars = '0123456789'
rules = []

def collect_word(line, op_chars_as_word):
    word = ""
    if len(line)<1: return ''
    if op_chars_as_word and line[0] in op_chars: return line[0]
    for c in line:
        if c == ' ' or (op_chars_as_word and c in op_chars): return word
        word += c
    return word

def collect_multiple_words(line):
    assert type(line) == str, f"Expected string, found {type(line)}"
    words = []
    word = ''
    while line != '':
        if line[0] == ' ': line = line[1:]
        word = collect_word(line, True)
        words.append(word)
        line = line[len(word):]
    return words

def eval_and_calc(expression):
    cnum = 0
    cexp = ''
    words = collect_multiple_words(expression)
    for n in words:
        if n in '+-*/':
            cexp = n
        elif n.isnumeric:
            if cexp == '':
                cnum = float(n)
            elif cexp == '+':
                cnum += float(n)
            elif cexp == '-':
                cnum -= float(n)
            elif cexp == '*':
                cnum *= float(n)
            elif cexp == '/':
                cnum /= float(n)
    return cnum

def replace_with_generic_names(known_names, e, i):
    generic_name = ''
    a = False
    dont_replace = False
    words = collect_multiple_words(e)
    for c in words:
        if dont_replace:
            dont_replace = False
            generic_name += c
            continue
        elif c not in op_chars:
            for name in known_names:
                if name[0] == c:
                    generic_name += name[1] 
                    a = True
            if a: continue
            known_names.append((c,chr(65+i)))
            generic_name += chr(65+i)
            i += 1
        elif c == '$':
            dont_replace = True
        else: generic_name += c
    return known_names, generic_name, i


def reverse_string(string):
    rev = ''
    l = len(string)
    while l > 0:
        l -= 1
        rev += string[l]
    return rev

def collect_between_delim(line, delim):
    line = reverse_string(line)
    collect = False
    cont = ''
    for c in line:
        if collect:
            if c == delim[1]:
                collect = False
            if not collect:
                return reverse_string(cont)
            if c not in delim:
                cont += c
        if c == delim[0]:
            collect = True

def replace_with_specific_names(known_names, expr):
    specific_name = ''
    calc_expr = ''
    if '{' in expr:
        calc_expr = collect_between_delim(expr, '}{')
    for c in expr:
        if c in name_chars and c not in num_chars:
            for n in known_names:
                if c == n[1]:
                    specific_name += n[0] 
        else:
            specific_name += c
    if calc_expr != '':
        calc_expr = replace_with_specific_names(known_names, calc_expr)
        evaluated = eval_and_calc(calc_expr)
        specific_name = specific_name.replace('{'+calc_expr+'}', str(evaluated))
    return specific_name

def define_rule(rule):
    if '->' not in rule:
        print("\033[31m  Error: expected `->` in definition\033[0m")
        return -1
    l, r = rule.replace(' ','').split('->')
    rules.append((l, r))

def apply_rule(expr, known_names):
    for r in rules:
        if expr == r[0]:
            rule_applied = replace_with_specific_names(known_names, r[1])
            return rule_applied
    return -1

def eval_expression(line, recurse_flag, rdep, print_col): 
    l = line.replace(' ','')
    i = 0
    known_names = []
    if '[' in l:
        in_brackets = collect_between_delim(l, '][')
        known_names, gb, i = replace_with_generic_names([], in_brackets, i)
        l = l.replace("["+in_brackets+"]", apply_rule(gb, known_names))

        eval_expression(in_brackets, True, rdep, "\033[33m")
        eval_expression(l, True, rdep, "\033[32m")
        return
    known_names, gl, i = replace_with_generic_names(known_names, l, i)
    rule_applied = apply_rule(gl, known_names)
    if rule_applied == -1:
        return
    print(f"  {print_col}{l} -> {rule_applied}\033[0m")

    if recurse_flag:
        if rdep > 256:
            print("  \033[31mMaximum recursion depth reached!\033[0m")
            return
        eval_expression(rule_applied, True, rdep + 1, print_col)

def load_file(file):
    if not exists(file):
        print(f"Error: file `{file}` does not exist")
        return
    input_file = open(file, 'r')
    for line in input_file:
        define_rule(line.strip('\n'))

def print_help():
    print("Options:")
    print("   define [expr]->[expr] - define a new rule")
    print("   rules                 - print out rules")
    print("   norec [expr]          - do not apply recursion")
    print("   load [file]           - load rule file")
    print("   [expr]                - evaluate expression with recursion")
    print("   quit                  - exit the program")
    print("")
    print("When defining a rule it is possible to set arithmetic operations")
    print("to be calculated within `{}` (define A->{A+1})")
    print("")
    print("To prevent a number from being parsed as a variable prefix with `$`")

while True:
    line = input("gum> ")
    if line == "quit": exit()
    elif collect_word(line, False) == "define":
        define_rule(line[7:])
    elif collect_word(line, False) == "rules":
        for rule in rules:
            print(f"  {rule[0]} -> {rule[1]}")
    elif collect_word(line, False) == "norec":
        eval_expression(line[6:], False, 0, "\033[32m")
    elif collect_word(line, False) == "load":
        load_file(collect_multiple_words(line)[1])
    elif collect_word(line, False) == "help":
        print_help()
    else:
        eval_expression(line, True, 0, "\033[32m")
