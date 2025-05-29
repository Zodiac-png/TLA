import re
from collections import defaultdict

class Grammar:
    def __init__(self,grammar_text):
        self.start_symbol = ''
        self.non_terminals = set()
        self.terminals = set()
        self.productions = defaultdict(list)

        self._parse_grammar(grammar_text)

    def _parse_grammar(self,text):
        lines = text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('START'):
                self.start_symbol = line.split('=')[1].strip()
            elif line.startswith('NON_TERMINALS'):
                symbols = line.split('=')[1].strip()
                self.non_terminals = set(s.strip() for s in symbols.split(','))
            elif line.startswith('TERMINALS'):
                symbols = line.split('=')[1].strip()
                self.terminals = set(s.strip() for s in symbols.split(','))
            elif '->' in line:
                left, right = map(str.strip, line.split('->', 1))
                alternatives = [alt.strip() for alt in re.split(r'\s*\|\s*', right)]
                for alt in alternatives:
                    self.productions[left].append(alt)

    def display(self):
        print('Start Symbol:',self.start_symbol)
        print('Non_Terminals:',self.non_terminals)
        print('Terminals:',self.terminals)
        print('Productions:')
        for head , bodies in self.productions.items():
            for body in bodies:
                print(f' {head} -> {body}')

class LL1Helper:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.first = {symbol: set() for symbol in grammar.non_terminals}
        self.follow = {symbol: set() for symbol in grammar.non_terminals}
        self._compute_first()
        self._compute_follow()

    def _compute_first(self):
        changed = True
        while changed:
            changed = False
            for head in self.grammar.productions:
                for body in self.grammar.productions[head]:
                    symbols = body.split()

                    i = 0
                    nullable = True
                    while i < len(symbols) and nullable:
                        symbol = symbols[i]
                        if symbol in self.grammar.terminals:
                            if symbol not in self.first[head]:
                                self.first[head].add(symbol)
                                changed = True
                            nullable = False
                        elif symbol in self.grammar.non_terminals:
                            before = len(self.first[head])
                            self.first[head].update(self.first[symbol] - {'eps'})
                            if 'eps' in self.first[symbol]:
                                nullable = True
                            else:
                                nullable = False
                            if len(self.first[head]) > before:
                                changed = True
                        elif symbol == 'eps':
                            if 'eps' not in self.first[head]:
                                self.first[head].add('eps')
                                changed = True
                            nullable = False
                        else:
                            nullable = False
                        i += 1

                    if nullable:
                        if 'eps' not in self.first[head]:
                            self.first[head].add('eps')
                            changed = True


    def _compute_follow(self):
        self.follow[self.grammar.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            for head in self.grammar.productions:
                for body in self.grammar.productions[head]:
                    symbols = body.split()
                    for i in range(len(symbols)):
                        B = symbols[i]
                        if B in self.grammar.non_terminals:
                            follow_before = len(self.follow[B])
                            beta = symbols[i + 1:] if i + 1 < len(symbols) else []
                            if beta:
                                first_beta = self._first_of_string(beta)
                                self.follow[B].update(first_beta - {'eps'})
                                if 'eps' in first_beta:
                                    self.follow[B].update(self.follow[head])
                            else:
                                self.follow[B].update(self.follow[head])
                            if len(self.follow[B]) > follow_before:
                                changed = True

    def _first_of_string(self, symbols):
        result = set()
        for symbol in symbols:
            if symbol in self.grammar.terminals:
                result.add(symbol)
                break
            elif symbol in self.grammar.non_terminals:
                result.update(self.first[symbol] - {'eps'})
                if 'eps' not in self.first[symbol]:
                    break
            elif symbol == 'eps':
                result.add('eps')
                break
        else:
            result.add('eps')
        return result

    def display_first(self):
        print("First sets:")
        for symbol in self.grammar.non_terminals:
            print(f"First({symbol}) = {{ {', '.join(self.first[symbol])} }}")

    def display_follow(self):
        print("\nFollow sets:")
        for symbol in self.grammar.non_terminals:
            print(f"Follow({symbol}) = {{ {', '.join(self.follow[symbol])} }}")


class LL1ParsingTable:
    def __init__(self, grammar: Grammar, first_sets, follow_sets):
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = defaultdict(dict)  # raw table: table[NT][t] = body
        self._build_table()

    def _build_table(self):
        for head in self.grammar.productions:
            for body in self.grammar.productions[head]:
                symbols = body.split()
                first_body = self._first_of_string(symbols)

                for terminal in first_body - {'eps'}:
                    self.table[head][terminal] = body

                if 'eps' in first_body:
                    for terminal in self.follow[head]:
                        self.table[head][terminal] = body

    def _first_of_string(self, symbols):
        result = set()
        for symbol in symbols:
            if symbol in self.grammar.terminals:
                result.add(symbol)
                break
            elif symbol in self.grammar.non_terminals:
                result.update(self.first[symbol] - {'eps'})
                if 'eps' not in self.first[symbol]:
                    break
            elif symbol == 'eps':
                result.add('eps')
                break
        else:
            result.add('eps')
        return result

    def get_table(self):
        # flat dict for use in DPDAParser
        result = {}
        for nt in self.table:
            for t in self.table[nt]:
                body = self.table[nt][t]
                result[(nt, t)] = f"{nt} -> {body}"
        return result

    def display(self):
        print("\nLL1 Parsing Table:")
        for nt in self.grammar.non_terminals:
            for t in self.grammar.terminals.union({'$'}):
                if t in self.table[nt]:
                    production = self.table[nt][t]
                    print(f"M[{nt}, {t}] = {nt} -> {production}")

class ParseTreeNode:
    def __init__(self, symbol, value=None, children=None):
        self.symbol = symbol
        self.value = value  # برای برگ‌های IDENTIFIER و LITERAL
        self.children = children if children else []

    def display(self, level=0):
        indent = "  " * level
        if self.value:
            print(f"{indent}{self.symbol}: {self.value}")
        else:
            print(f"{indent}{self.symbol}")
        for child in self.children:
            child.display(level + 1)

class DPDAParser:
    def __init__(self, grammar: Grammar, parse_table):
        self.grammar = grammar
        self.parse_table = parse_table

    def parse_with_tree(self, tokens):
        stack = [('$', None)]
        stack.append((self.grammar.start_symbol, None))
        input_tokens = tokens + [('$', None)]
        index = 0

        print("\n📘 Parsing Steps (with parse tree):")
        root = None

        while stack:
            top_symbol, parent_node = stack.pop()
            current_token, current_value = input_tokens[index]
            print(f"Top: {top_symbol}, Current: {current_token}({current_value}), Stack: {[s[0] for s in stack]}")

            if top_symbol == current_token:
                print(f"✔️ Matched: {current_token}({current_value})")
                index += 1
                leaf_node = ParseTreeNode(current_token, current_value)
                if parent_node:
                    parent_node.children.append(leaf_node)
                continue

            elif top_symbol in self.grammar.terminals or top_symbol == '$':
                print(f"❌ Error: Expected '{top_symbol}', but found '{current_token}'.")
                return None

            key = (top_symbol, current_token)
            if key not in self.parse_table:
                print(f"❌ Error: No rule for ({top_symbol}, {current_token}).")
                return None

            rule = self.parse_table[key]
            _, rhs = rule.split('->')
            rhs_symbols = rhs.strip().split()
            print(f"🔄 Applying Rule: {rule}")

            current_node = ParseTreeNode(top_symbol)
            if parent_node:
                parent_node.children.append(current_node)
            else:
                root = current_node  # set as root

            if rhs_symbols != ['eps']:
                for sym in reversed(rhs_symbols):
                    stack.append((sym, current_node))

        if index == len(input_tokens):
            print("✅ Input was successfully parsed.")
            return root
        else:
            print("❌ Error: Input not fully consumed.")
            return None

class Lexer:
    def __init__(self):
        self.token_specs = [
            ('FUNCTION', r'function'),
            ('IF', r'if'),
            ('WHILE', r'while'),
            ('RETURN', r'return'),
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('LEFT_PAR', r'\('),
            ('RIGHT_PAR', r'\)'),
            ('LEFT_BRACE', r'\{'),
            ('RIGHT_BRACE', r'\}'),
            ('EQUALS', r'='),
            ('SEMICOLON', r';'),
            ('PLUS', r'\+'),
            ('MINUS', r'-'),
            ('STAR', r'\*'),
            ('SLASH', r'/'),
            ('LITERAL', r'\d+(\.\d+)?'),
            ('WHITESPACE', r'\s+'),
        ]

        self.regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_specs)

    def tokenize(self, text):
        tokens = []
        for match in re.finditer(self.regex, text):
            kind = match.lastgroup
            if kind == 'WHITESPACE':
                continue
            value = match.group()
            tokens.append((kind, value))
        return tokens

def rename_identifier(tokens, old_name, new_name):
    renamed_tokens = []
    for kind, value in tokens:
        if kind == 'IDENTIFIER' and value == old_name:
            renamed_tokens.append((kind, new_name))
        else:
            renamed_tokens.append((kind, value))
    return renamed_tokens

def rename_in_parse_tree(node, old_name, new_name):
    if node.symbol == 'IDENTIFIER' and node.value == old_name:
        node.value = new_name
    for child in node.children:
        rename_in_parse_tree(child, old_name, new_name)

# ------------- مثال استفاده -------------

grammar_text = """
START = E
NON_TERMINALS = E, E_prime, T, T_prime, F
TERMINALS = IDENTIFIER, LITERAL, PLUS, STAR, LEFT_PAR, RIGHT_PAR
E -> T E_prime
E_prime -> PLUS T E_prime | eps
T -> F T_prime
T_prime -> STAR F T_prime | eps
F -> LEFT_PAR E RIGHT_PAR | IDENTIFIER | LITERAL
"""

grammar = Grammar(grammar_text)
grammar.display()

helper = LL1Helper(grammar)
helper.display_first()
helper.display_follow()

table_obj = LL1ParsingTable(grammar, helper.first, helper.follow)
table_obj.display()
parse_table = table_obj.get_table()

lexer = Lexer()
code = "x + 5 * ( y + 1 )"
tokens = lexer.tokenize(code)
print("\nTokens:", tokens)

parser = DPDAParser(grammar, parse_table)
parse_tree = parser.parse_with_tree(tokens)

if parse_tree:
    print("\nParse Tree before rename:")
    parse_tree.display()

    # Rename identifier x -> var_1
    rename_in_parse_tree(parse_tree, 'x', 'var_1')

    print("\nParse Tree after rename (x -> var_1):")
    parse_tree.display()

    # Rename identifier y -> var_2
    rename_in_parse_tree(parse_tree, 'y', 'var_2')

    print("\nParse Tree after rename (y -> var_2):")
    parse_tree.display()

    # همچنین rename توکن‌ها را هم می‌تونیم انجام بدیم
    tokens_renamed = rename_identifier(tokens, 'x', 'var_1')
    tokens_renamed = rename_identifier(tokens_renamed, 'y', 'var_2')
    print("\nTokens after rename:", tokens_renamed)
