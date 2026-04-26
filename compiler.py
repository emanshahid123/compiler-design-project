import re
 
# =========================================================
# PHASE 1: LEXER
# Converts source code into tokens using regex
# =========================================================
 
TOKEN_SPEC = [
    ('INT',       r'\bint\b'),
    ('IF',        r'\bif\b'),
    ('ELSE',      r'\belse\b'),
    ('WHILE',     r'\bwhile\b'),
    ('NUMBER',    r'\d+'),
    ('ID',        r'[a-zA-Z_]\w*'),
    ('EQ',        r'=='), ('NEQ', r'!='),
    ('LEQ',       r'<='), ('GEQ', r'>='),
    ('LT',        r'<'),  ('GT',  r'>'),
    ('ASSIGN',    r'='),  ('SEMI', r';'),
    ('LPAREN',    r'\('), ('RPAREN', r'\)'),
    ('LBRACE',    r'\{'), ('RBRACE', r'\}'),
    ('PLUS',      r'\+'), ('MINUS', r'-'),
    ('MUL',       r'\*'), ('DIV',   r'/'),
    ('SKIP',      r'[ \t\n\r]+'),
    ('BAD',       r'.'),
]
 
def lexer(code):
    regex  = '|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_SPEC)
    tokens = []
    line   = 1
    for m in re.finditer(regex, code):
        kind, val = m.lastgroup, m.group()
        if kind == 'SKIP':  line += val.count('\n')
        elif kind == 'BAD': raise SyntaxError(f"[Lexer] Line {line}: unknown char '{val}'")
        else:               tokens.append((kind, val, line))
    return tokens
 
 
# =========================================================
# PHASE 3: SYMBOL TABLE
# Tracks declared variables per scope
# =========================================================
 
class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
 
    def enter(self): self.scopes.append({})
    def exit(self):  self.scopes.pop()
 
    def declare(self, name, line):
        if name in self.scopes[-1]:
            raise Exception(f"[Semantic] Line {line}: '{name}' already declared")
        self.scopes[-1][name] = 'int'
 
    def check(self, name, line):
        if not any(name in s for s in self.scopes):
            raise Exception(f"[Semantic] Line {line}: '{name}' not declared")
 
    def show(self):
        print("+----------------+------+--------+")
        print(f"| {'Name':<14} | Type | Scope  |")
        print("+----------------+------+--------+")
        for i, scope in enumerate(self.scopes):
            label = 'global' if i == 0 else f'local{i}'
            for name in scope:
                print(f"| {name:<14} | int  | {label:<6} |")
        print("+----------------+------+--------+")
 
 
# =========================================================
# PHASE 4: IR GENERATION
# Emits Three-Address Code (TAC) instructions
# =========================================================
 
ir   = []
tc   = 1    # temp counter
lc   = 1    # label counter
 
def tmp():
    global tc; t = f"t{tc}"; tc += 1; return t
 
def lbl():
    global lc; l = f"L{lc}"; lc += 1; return l
 
def emit(op, a='', b='', r=''):
    ir.append((op, a, b, r))
 
def show_ir():
    INV = {'==':'!=','!=':'==','<':'>=','>':'<=','<=':'>','>=':'<'}
    print("\n--- Intermediate Representation (TAC) ---")
    for op, a, b, r in ir:
        if   op == 'LABEL':  print(f"  {a}:")
        elif op == 'ASSIGN': print(f"  {r} = {a}")
        elif op == 'GOTO':   print(f"  goto {a}")
        elif op in INV:      print(f"  if {a} {op} {b} goto {r}")
        else:                print(f"  {r} = {a} {op} {b}")
 
 
# =========================================================
# PHASE 2: RECURSIVE DESCENT PARSER
# Each method = one grammar rule
# =========================================================
 
class Parser:
    def __init__(self, tokens):
        self.tok = tokens
        self.pos = 0
        self.sym = SymbolTable()
 
    # ── Helpers ───────────────────────────────────────────
 
    def cur(self):   return self.tok[self.pos] if self.pos < len(self.tok) else ('EOF','EOF',-1)
    def typ(self):   return self.cur()[0]
    def val(self):   return self.cur()[1]
    def line(self):  return self.cur()[2]
 
    def eat(self, expected=None):
        t = self.cur()
        if expected and t[0] != expected:
            raise SyntaxError(f"[Syntax] Line {t[2]}: expected '{expected}', got '{t[1]}'")
        self.pos += 1
        return t
 
    # ── Grammar rules ─────────────────────────────────────
 
    def program(self):
        self.stmts()
 
    def stmts(self):
        while self.typ() not in ('EOF', 'RBRACE'):
            self.stmt()
 
    def stmt(self):
        t = self.typ()
        if   t == 'INT':   self.decl()
        elif t == 'ID':    self.assign()
        elif t == 'IF':    self.if_stmt()
        elif t == 'WHILE': self.while_stmt()
        else: raise SyntaxError(f"[Syntax] Line {self.line()}: unexpected '{self.val()}'")
 
    def decl(self):
        self.eat('INT')
        name, line = self.val(), self.line()
        self.eat('ID')
        self.sym.declare(name, line)
        if self.typ() == 'ASSIGN':
            self.eat('ASSIGN')
            v = self.expr()
            emit('ASSIGN', v, '', name)
        self.eat('SEMI')
 
    def assign(self):
        name, line = self.val(), self.line()
        self.eat('ID')
        self.sym.check(name, line)
        self.eat('ASSIGN')
        v = self.expr()
        emit('ASSIGN', v, '', name)
        self.eat('SEMI')
 
    def if_stmt(self):
        self.eat('IF'); self.eat('LPAREN')
        left, op, right = self.condition()
        self.eat('RPAREN')
 
        INV = {'==':'!=','!=':'==','<':'>=','>':'<=','<=':'>','>=':'<'}
        L_true, L_false, L_end = lbl(), lbl(), lbl()
 
        emit(INV[op], left, right, L_false)     # jump to false branch if condition fails
        emit('LABEL', L_true)
        self.sym.enter(); self.eat('LBRACE'); self.stmts(); self.eat('RBRACE'); self.sym.exit()
        emit('GOTO', L_end)
        emit('LABEL', L_false)
        if self.typ() == 'ELSE':
            self.eat('ELSE')
            self.sym.enter(); self.eat('LBRACE'); self.stmts(); self.eat('RBRACE'); self.sym.exit()
        emit('LABEL', L_end)
 
    def while_stmt(self):
        self.eat('WHILE'); self.eat('LPAREN')
        L_start, L_body, L_end = lbl(), lbl(), lbl()
 
        emit('LABEL', L_start)
        left, op, right = self.condition()
        self.eat('RPAREN')
 
        INV = {'==':'!=','!=':'==','<':'>=','>':'<=','<=':'>','>=':'<'}
        emit(INV[op], left, right, L_end)       # exit loop if condition fails
        emit('LABEL', L_body)
        self.sym.enter(); self.eat('LBRACE'); self.stmts(); self.eat('RBRACE'); self.sym.exit()
        emit('GOTO', L_start)                   # loop back
        emit('LABEL', L_end)
 
    def condition(self):
        left = self.expr()
        if self.typ() not in ('EQ','NEQ','LT','GT','LEQ','GEQ'):
            raise SyntaxError(f"[Syntax] Line {self.line()}: expected comparison operator")
        OP = {'EQ':'==','NEQ':'!=','LT':'<','GT':'>','LEQ':'<=','GEQ':'>='}
        op = OP[self.eat()[0]]
        return left, op, self.expr()
 
    # expr -> term ((+|-) term)*
    def expr(self):
        v = self.term()
        while self.typ() in ('PLUS', 'MINUS'):
            op = self.eat()[1]
            r  = self.term()
            t  = tmp(); emit(op, v, r, t); v = t
        return v
 
    # term -> factor ((*|/) factor)*
    def term(self):
        v = self.factor()
        while self.typ() in ('MUL', 'DIV'):
            op = self.eat()[1]
            r  = self.factor()
            t  = tmp(); emit(op, v, r, t); v = t
        return v
 
    def factor(self):
        t = self.cur()
        if t[0] == 'NUMBER':
            self.eat(); return t[1]
        elif t[0] == 'ID':
            self.sym.check(t[1], t[2]); self.eat(); return t[1]
        elif t[0] == 'LPAREN':
            self.eat('LPAREN'); v = self.expr(); self.eat('RPAREN'); return v
        raise SyntaxError(f"[Syntax] Line {t[2]}: expected number or variable, got '{t[1]}'")
 
 
# =========================================================
# MAIN — run all phases
# =========================================================
 
source = """
int x;
int y;
int z;
int result;
 
x = 10;
y = 3;
z = x + y * 2;
 
if (z > 15) {
    result = z - 5;
} else {
    result = z + 5;
}
 
int counter;
counter = 0;
 
while (counter < 3) {
    counter = counter + 1;
}
"""
 
print("=== PHASE 1: TOKENS ===")
tokens = lexer(source)
print(f"{'Type':<12} {'Value':<12} Line")
print("-" * 32)
for kind, val, line in tokens:
    print(f"{kind:<12} {val:<12} {line}")
 
print("\n=== PHASE 2-3-4: PARSE + SEMANTICS + IR ===")
p = Parser(tokens)
p.program()
print("Parsing complete — no errors.")
 
show_ir()
 
print("\n=== PHASE 3: SYMBOL TABLE ===")
p.sym.show()
 