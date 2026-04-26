import re

# =========================================================
# 🔹 PHASE 1: LEXICAL ANALYSIS (LEXER)
# This defines token rules using regular expressions
# =========================================================
TOKEN_SPEC = [
    ('INT', r'\bint\b'),
    ('WHILE', r'\bwhile\b'),
    ('NUMBER', r'\d+'),
    ('ID', r'[a-zA-Z_]\w*'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('MUL', r'\*'),
    ('DIV', r'/'),
    ('ASSIGN', r'='),
    ('SEMICOLON', r';'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('GT', r'>'),
    ('SKIP', r'[ \t\n]+'),
]

# 🔹 Lexer function → converts source code into tokens
def lexer(code):
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
    tokens = []

    for match in re.finditer(tok_regex, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'SKIP':
            continue

        tokens.append((kind, value))  # Output tokens

    return tokens


# =========================================================
# 🔹 PHASE 3: SEMANTIC ANALYSIS (SYMBOL TABLE)
# Stores variables and checks correctness
# =========================================================
symbol_table = {}

# Add variable to symbol table
def declare(var):
    symbol_table[var] = 'int'

# Check if variable is declared
def check(var):
    if var not in symbol_table:
        raise Exception(f"Error: Variable '{var}' not declared")


# =========================================================
# 🔹 PHASE 4: INTERMEDIATE CODE GENERATION (IR)
# Generates temporary variables and instructions
# =========================================================
temp_count = 1

def new_temp():
    global temp_count
    t = f"t{temp_count}"
    temp_count += 1
    return t


# =========================================================
# 🔹 PHASE 2: SYNTAX ANALYSIS (PARSER)
# Checks grammar rules and structure of code
# =========================================================
def parse(tokens):
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # 🔸 Declaration: int a;
        if token[0] == 'INT':
            var = tokens[i+1][1]
            declare(var)   # Semantic: store variable
            i += 3

        # 🔸 Assignment statement
        elif token[0] == 'ID':
            var = token[1]
            check(var)     # Semantic: check variable exists

            # Syntax check
            if tokens[i+1][0] != 'ASSIGN':
                raise Exception("Syntax Error")

            val1 = tokens[i+2][1]

            # 🔸 Simple assignment
            if tokens[i+3][0] == 'SEMICOLON':
                print(f"{var} = {val1}")   # IR output
                i += 4

            # 🔸 Expression assignment
            else:
                op = tokens[i+3][1]
                val2 = tokens[i+4][1]

                t = new_temp()   # IR: create temp variable
                print(f"{t} = {val1} {op} {val2}")
                print(f"{var} = {t}")
                i += 6
        else:
            i += 1


# =========================================================
# 🔹 MAIN PROGRAM (COMPILER EXECUTION)
# Runs all phases step-by-step
# =========================================================

code = """
int a;
int b;
int c;

a = 5+8;
b = a + 3;
c = b * 8;
"""

# 🔹 Phase 1: Lexical Analysis
tokens = lexer(code)

print("TOKENS:")
for t in tokens:
    print(t)

# 🔹 Phase 2 + 3 + 4:
# Parser + Semantic + IR
print("\nINTERMEDIATE CODE:")
parse(tokens)

# 🔹 Display Symbol Table (Semantic Output)
print("\nSYMBOL TABLE:")
print("+------------+----------+")
print("| Variable   | Type     |")
print("+------------+----------+")

for var, typ in symbol_table.items():
    print(f"| {var:<10} | {typ:<8} |")

print("+------------+----------+")