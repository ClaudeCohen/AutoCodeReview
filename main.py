#! /usr/bin/env python
"""
This is an automated tool to run codding conventions checkers and output it into
a Code Review also known as a CR.
This tool is built around pep8 and python but will be changed in the future to
support other conventions checkers as well.
"""

import sys
import subprocess
import re
PEP8_COMMAND_LINE = "pep8 %s"
PYLINT_COMMAND_LINE = "pylint %s"
CR_COMMENT_LINE = "# CR: %s\n"
# Notice I cancel "Line too long" because pylint and pep8 both comment on it.
# Notice I only cancel one kind of "line to long" not both.
IGNORED_CR_COMMENTS = ["Missing docstring",
                       "Line too long",
                       ]


def main(filename):
    cr_lines = generate_cr_lines(filename)
    cr_lines.sort()
    cr_lines = filter_cr_lines(cr_lines)
    apply_cr_lines(filename, cr_lines)


def filter_cr_lines(cr_lines):
    return [line for line in cr_lines if not should_filter_cr_comment(line)]


def should_filter_cr_comment(cr_tuple):
    for text in IGNORED_CR_COMMENTS:
        if text in cr_tuple[2]:
            return True
    return False


def apply_cr_lines(filename, cr_lines):
    """
    This function merges the list of cr comments into the original file.
    It does it by creating 2 lists of tuples, each of them in the next format
    (line number, line text)
    then extends the list and sort them. The default sort is by the first item
    in the tuple.  Later it writes the lines to the output file.
    """
    file_lines = open(filename).readlines()
    cr_lines = [(cr[0], create_cr_comment(cr[2])) for cr in cr_lines]

    # I add 1 here because enumerate is zero based and line numbers in file are
    # 1 based. I add 0.5 more to make sure that the CR comments about lines will
    # come before the lines (having lower index by 0.5)
    file_lines_with_numbers = [(line_number + 1.5, line) for line_number, line in enumerate(file_lines)]
    cr_lines.extend(file_lines_with_numbers)
    cr_lines.sort()

    new_file_lines = [line for number, line in cr_lines]

    with open("%s.cr" % filename, "w") as checked_file:
        checked_file.writelines(new_file_lines)


def create_cr_comment(tool_comment):
    return CR_COMMENT_LINE % (tool_comment,)


def generate_cr_lines(filename):
    convetions_tool_output = get_pep8_cr_lines(filename)
    convetions_tool_output.extend(get_pylint_cr_lines(filename))
    return convetions_tool_output


# This is the format of each output line we care about in pylint
# C: 71,0: Line too long (87/80)
def get_pylint_cr_lines(filename):
    cr_comments_list = []
    command_line = PYLINT_COMMAND_LINE % (filename,)
    tool_output = shell(command_line)
    for line in tool_output:
        line_parts = re.match("[A-Z]: (?P<line_number>\d*),(?P<column_number>\d*):(?P<description>.*)", line)
        if not line_parts:
            # if line is not the right format
            continue
        line_number = line_parts.group('line_number')
        description = line_parts.group('description')
        cr_comments_list.append((int(line_number), "pylint", description))
    return cr_comments_list


def get_pep8_cr_lines(filename):
    cr_comments_list = []
    command_line = PEP8_COMMAND_LINE % (filename,)
    tool_output = shell(command_line)

    number_of_semicolons_in_filename = filename.count(":")
    for line in tool_output:
        if not line:
            continue
        splited_line = line.split(":")[number_of_semicolons_in_filename:]
        line_number = splited_line[-3]
        error_and_text = splited_line[-1].lstrip()
        error_code = error_and_text.split(" ")[0]
        error_text = " ".join(error_and_text.split(" ")[1:])
        cr_comments_list.append((int(line_number), error_code, error_text))
    return cr_comments_list


def shell(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except Exception, e:
        output = str(e.output)
        finished = output.split('\n')
        return finished

if "__main__" == __name__:
    main(sys.argv[1])
