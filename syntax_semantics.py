# CS 413 - Laboratory Activity No. 2
# From Syntax to Semantics: Building a Grammar Checker and Evaluator
#
# Grammar being implemented:
#   <expr>   -> <term> { (+ | -) <term> }
#   <term>   -> <factor> { (* | /) <factor> }
#   <factor> -> ( <expr> ) | <digit>
#   <digit>  -> 0|1|2|3|4|5|6|7|8|9
#
# This file is synced 1:1 with Flowchart.drawio / Flowchart.png:
# every comment below quotes the exact box or diamond label from the
# flowchart, in the same order they appear on the diagram, so each
# lane of the flowchart (MAIN PROGRAM, expr(), term(), factor()) can
# be read side by side with the matching function.


# ---------------------------------------------------------------
# Error type
# ---------------------------------------------------------------

class BadSyntax(Exception):
    """Raised when the input does not follow the grammar."""

    def __init__(self, position, message):
        self.position = position   # where the error was found
        self.message = message     # what went wrong
        super().__init__(message)


# ---------------------------------------------------------------
# The parser
# ---------------------------------------------------------------

class Parser:

    def __init__(self, text):
        self.text = text
        self.pos = 0        # index of the next character to read

    def peek(self):
        """Return the next character without using it up. Skips spaces."""
        while self.pos < len(self.text) and self.text[self.pos] == " ":
            self.pos += 1
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None         # None means we reached the end of the input

    def take(self):
        """Return the next character and move past it."""
        character = self.peek()
        self.pos += 1
        return character

    # =============================================================
    # FLOWCHART LANE: expr()      <expr> -> <term> { ( + | - ) <term> }
    # =============================================================
    def expr(self):
        # Box: "Run  term()"
        value = self.term()

        # Diamond: "Is the next character + or - ?"
        #   yes -> "Take the operator, run term() again, add or subtract"
        #          then loop back to "Run term()" (the "repeat" arrow)
        #   no  -> "Return the expr value"
        while self.peek() in ("+", "-"):
            # Box: "Take the operator, run term() again, add or subtract"
            operator = self.take()
            right = self.term()          # "run term() again" / repeat
            if operator == "+":
                value = value + right
            else:
                value = value - right

        # Oval: "Return the expr value"
        return value

    # =============================================================
    # FLOWCHART LANE: term()      <term> -> <factor> { ( * | / ) <factor> }
    # =============================================================
    def term(self):
        # Box: "Run  factor()"
        value = self.factor()

        # Diamond: "Is the next character * or / ?"
        #   yes -> "Take the operator, run factor() again, multiply or divide"
        #          then loop back to "Run factor()" (the "repeat" arrow)
        #   no  -> "Return the term value"
        while self.peek() in ("*", "/"):
            # Box: "Take the operator, run factor() again, multiply or divide"
            operator = self.take()
            right = self.factor()        # "run factor() again" / repeat
            if operator == "*":
                value = value * right
            else:
                if right == 0:
                    raise BadSyntax(self.pos, "cannot divide by zero")
                value = value / right

        # Oval: "Return the term value"
        return value

    # =============================================================
    # FLOWCHART LANE: factor()    <factor> -> ( <expr> ) | <digit>
    # =============================================================
    def factor(self):
        character = self.peek()

        # Not its own box on the diagram, but needed so the digit check
        # below never crashes on None; falls into the same
        # "ERROR / report the position" oval as the other "no" branches
        # on this lane.
        if character is None:
            raise BadSyntax(self.pos, "input ended early, expected a digit or (")

        # Diamond: "Is the next character a digit 0-9 ?"   -- yes branch
        # Box: "Take the digit (stops the recursion)"
        # Oval: "Return the value"
        if character.isdigit():
            self.take()
            return int(character)

        # Diamond: "Is the next character a digit 0-9 ?"   -- no branch,
        # goes to the next diamond:
        # Diamond: "Is the next character ( ?"              -- yes branch
        if character == "(":
            # Box: "Take the ("
            self.take()

            # Box: "RECURSION: run  expr()  again"
            # (the red dashed arrow on the diagram -- factor() calls back
            # up to expr() so a whole expression can sit inside the
            # parentheses)
            value = self.expr()

            # Diamond: "Is the next character ) ?"
            #   no  -> "ERROR / report the position"
            #   yes -> "Take the )" -> "Return the value"
            if self.peek() != ")":
                raise BadSyntax(self.pos, "missing closing parenthesis )")
            self.take()
            return value

        # Diamond: "Is the next character ( ?"   -- no branch
        # Oval: "ERROR / report the position"
        # (anything else cannot start a factor, like the second + in 3++4)
        raise BadSyntax(self.pos, "unexpected character '" + character + "'")

    # =============================================================
    # FLOWCHART LANE: MAIN PROGRAM
    # "Run  expr()" -> "Was an error found?" -> "Were all characters
    # used up?" -> VALID SYNTAX / INVALID SYNTAX
    # =============================================================
    def parse(self):
        """Check the whole input and return its value."""
        if self.text.strip() == "":
            raise BadSyntax(0, "the input is empty")

        # Box: "Run  expr()"
        # If expr() raises BadSyntax here, that IS the "Was an error
        # found? -> yes" branch: the exception propagates straight to
        # whoever called parse(), which prints INVALID SYNTAX.
        value = self.expr()

        # "Was an error found? -> no", so we move on to the next
        # diamond: "Were all characters used up?"
        # Without this check, something like 12 or 3+4) would be
        # wrongly accepted, because expr() itself would already be
        # satisfied and never notice the leftover text.
        leftover = self.peek()
        if leftover is not None:
            # "Were all characters used up? -> no" -> INVALID SYNTAX
            raise BadSyntax(self.pos, "extra character '" + leftover + "' at the end")

        # "Were all characters used up? -> yes" -> VALID SYNTAX
        return value


# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------

def evaluate(text):
    """Run the parser on one string and return the answer.

    This is the MAIN PROGRAM lane end to end: "Read the input string"
    happens where the caller builds the string, "Run expr()" and the
    two diamonds happen inside Parser.parse() above, and the caller
    (run_tests / main, below) is what actually prints VALID SYNTAX or
    INVALID SYNTAX depending on whether this raises BadSyntax.
    """
    return Parser(text).parse()


def show(value):
    """Print 4 instead of 4.0 when the answer is a whole number."""
    if value == int(value):
        return str(int(value))
    return str(value)


# ---------------------------------------------------------------
# Stretch requirement: the ambiguous grammar
# ---------------------------------------------------------------

def left_to_right(text):
    """Work out the answer left to right, ignoring precedence.

    This is what happens with the ambiguous grammar
    <expr> -> <expr> + <expr> | <expr> * <expr> | <digit>
    because nothing in that rule says which side to do first.
    """
    characters = text.replace(" ", "")
    value = int(characters[0])
    i = 1
    while i < len(characters):
        operator = characters[i]
        right = int(characters[i + 1])
        if operator == "+":
            value = value + right
        elif operator == "-":
            value = value - right
        elif operator == "*":
            value = value * right
        else:
            value = value / right
        i = i + 2
    return value


def show_ambiguity():
    text = "2+3*4"
    print("--- Ambiguity Demonstration ---")
    print("Expression:", text)
    print("Ambiguous grammar (left to right): ", show(left_to_right(text)), " -> reads it as (2+3)*4")
    print("Corrected grammar (this program):  ", show(evaluate(text)), " -> reads it as 2+(3*4)")
    print()
    print("The ambiguous rule lets 2+3*4 be built two different ways, so the")
    print("same input can give two different answers. The grammar in Section II")
    print("fixes this by putting <term> below <expr>. Because expr() has to go")
    print("through term() before it can do a + or -, every * and / is finished")
    print("first. That leaves only one way to read the expression, so the")
    print("answer is always 14.")
    print()


# ---------------------------------------------------------------
# Required test cases
# ---------------------------------------------------------------

def run_tests():
    tests = [
        ("3+4*2", "Valid", 11),
        ("(3+4)*2", "Valid", 14),
        ("8/2-1", "Valid", 3),
        ("3++4", "Invalid", None),
        ("(3+4", "Invalid", None),
        ("2+3*4", "Valid", 14),
    ]

    print("--- Required Test Cases ---")
    for text, expected, answer in tests:
        try:
            # Box: "Run  expr()" (via evaluate -> parse -> expr)
            result = evaluate(text)
            # Diamond: "Was an error found? -> no" and
            # Diamond: "Were all characters used up? -> yes"
            # Oval: "VALID SYNTAX / print the answer"
            print(text.ljust(10), "Valid  ", "Result:", show(result))
        except BadSyntax as error:
            # Diamond: "Was an error found? -> yes", OR
            # Diamond: "Were all characters used up? -> no"
            # Oval: "INVALID SYNTAX / print the position"
            print(text.ljust(10), "Invalid", "Error at position", error.position)
    print()


# ---------------------------------------------------------------
# Main program
# ---------------------------------------------------------------

def main():
    show_ambiguity()
    run_tests()

    print("--- Try it yourself (type quit to stop) ---")
    while True:
        # Box: "Read the input string"
        text = input("Enter expression: ")

        if text.strip().lower() == "quit":
            print("Program finished.")
            break

        try:
            # Task A: check the syntax.
            # Box: "Run  expr()" -> Diamond: "Was an error found?" ->
            # Diamond: "Were all characters used up?"
            result = evaluate(text)
            # Task B: only reached if Task A did not raise an error.
            # Oval: "VALID SYNTAX / print the answer"
            print("Valid syntax")
            print("Result:", show(result))
        except BadSyntax as error:
            # Oval: "INVALID SYNTAX / print the position"
            print("Invalid syntax")
            print("Error at position", error.position, "-", error.message)
        print()


main()
