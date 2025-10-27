from mpmath import mp
import argparse
import re


# Define command-line arguments
parser = argparse.ArgumentParser(
    description="""
        Calculates an expression with a given number of decimals, by default 100.
        
        To this end, all names are prefixed with "mp." and all numbers
        are converted to mpmath floats or complex numbers before
        evaluation. If this is undesirable, for example when defining
        a lambda function, names and numbers can be escaped with
        backslashes to prevent this.
    """
)
parser.add_argument("expression", help="The mathematical expression to evaluate.")
parser.add_argument("-d", "--digits", type=int, default=100, help="How many digits to calculate the result with.")
parser.add_argument("-a", "--all", "--all-digits", action="store_true", help="Print all digits, including trailing zeros.")
parser.add_argument("--debug", action="store_true", help="Print debug output.")


# Define regex patterns
allowed_characters = r"a-zA-Z0-9\s_:=" + re.escape(r"\().+-/*^&|,[]")
disallowed_characters = re.compile(f"[^{allowed_characters}]")

cannot_start_after = r"a-zA-Z\d_" + re.escape(r"\.")
# Names must start with letters or underscores
name_pattern = re.compile(rf"(?<![{cannot_start_after}])([a-zA-Z_][a-zA-Z0-9]*)", re.ASCII)
# Digits with optional underscores in between
int_pattern = r"\d[\d_]*(?<!_)"
# [-] integer [.fraction] [e[-]exponent] [j]
number_pattern = re.compile(
    rf"(?<![{cannot_start_after}])(-?{int_pattern}(?:\.{int_pattern})?(?:e-?{int_pattern})?)j?(?![a-zA-Z\d\._])",
    re.ASCII,
)

open_float_pattern = re.compile(r"((?<!\d)\.\d)|(\d\.(?!\d))", re.ASCII)  # 0. or .0, for example


# Define routine to replace number literals with mp.mpf floats, and save those in FLOATS
NUMBERS = {}
def replace_number_with_mpf(match: re.Match[str]) -> str:
    """Store the float as an mpf value and return how to obtain it."""
    global NUMBERS

    key = match[0]
    if not key in NUMBERS:
        NUMBERS[key] = mp.mpmathify(key)

    return f"NUMBERS['{key}']"


if __name__ == "__main__":
    args = parser.parse_args()
    expression = args.expression
    DIGITS = args.digits
    ALL_DIGITS = args.all
    DEBUG = args.debug

    if DEBUG: print(f"{'Input:':<25}", expression)

    if match := disallowed_characters.search(expression):
        raise ValueError(f"Character not allowed: {match[0]}")
    if open_float_pattern.search(expression):
        raise ValueError("Open floats ('123.' or '.123') are not allowed.")

    with mp.workdps(DIGITS):
        # Add mp. before names that are not escaped by backslashes
        expression = re.sub(name_pattern, r"mp.\1", expression)
        if DEBUG: print(f"{'Replaced names:':<25}", expression)

        # Convert numbers to mpf or mpc
        expression = re.sub(number_pattern, replace_number_with_mpf, expression)
        if DEBUG: print(f"{'Replaced numbers:':<25}", expression)
        if DEBUG: print(f"{'Contents of NUMBERS:':<25}", NUMBERS)

        # Strip backslashes
        expression = expression.replace("\\", "")
        if DEBUG: print(f"{'Removed backslashes:':<25}", expression)

        value = eval(expression, globals={"NUMBERS": NUMBERS, "mp": mp})
        if DEBUG:
            print("Result:", repr(value), sep="\n")
        elif ALL_DIGITS:
            try:
                mp.nprint(mp.mpmathify(value), DIGITS, strip_zeros=False)
            except TypeError:
                mp.nprint(value, DIGITS, strip_zeros=False)
        else:
            print(value)
