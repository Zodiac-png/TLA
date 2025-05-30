from collections import defaultdict
import re

# ----------- SpecParser Class -------------
class SpecParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.content = ""
        self.grammar_text = ""
        self.lexer_text = ""

    def load_spec(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.content = f.read()
        print(f"[INFO] Loaded spec file: {self.filepath}")

    def extract_sections(self):
        grammar_start = self.content.find("# === GRAMMAR ===")
        lexer_start = self.content.find("# === LEXER ===")

        if grammar_start == -1 or lexer_start == -1:
            raise ValueError("Spec file must contain both # === GRAMMAR === and # === LEXER === sections")

        self.grammar_text = self.content[grammar_start:lexer_start].strip()
        self.lexer_text = self.content[lexer_start:].strip()

        print("[INFO] Extracted GRAMMAR and LEXER sections")

    def clean_lexer(self):
        lines = self.lexer_text.splitlines()
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            if "->" in line:
                token_name, regex = line.split("->", 1)
                token_name = token_name.strip()
                regex = regex.strip()

                if regex.startswith("/") and regex.endswith("/"):
                    regex_body = regex[1:-1]

                    def clean_char_class(m):
                        content = m.group(1)
                        content_no_spaces = content.replace(" ", "")
                        return f"[{content_no_spaces}]"

                    regex_body = re.sub(r"\[([^\]]+)\]", clean_char_class, regex_body)
                    regex_body = re.sub(r"\s+", "", regex_body)

                    regex_cleaned = f"/{regex_body}/"
                    cleaned_lines.append(f"{token_name} -> {regex_cleaned}")
                else:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)

        self.lexer_text = "\n".join(cleaned_lines)
        print("[INFO] Cleaned LEXER regex patterns")

    def get_grammar(self):
        return self._extract_grammar_section()

    def get_lexer(self):
        return self._extract_lexer_section()

    def _extract_grammar_section(self):
        in_grammar = False
        grammar_lines = []
        for line in self.content.splitlines():
            line = line.strip()
            if line == "# === GRAMMAR ===":
                in_grammar = True
                continue
            if line.startswith("# === LEXER ==="):
                break
            if in_grammar and line and not line.startswith("#"):
                grammar_lines.append(line)
        return grammar_lines

    def _extract_lexer_section(self):
        in_lexer = False
        lexer_lines = []
        for line in self.content.splitlines():
            line = line.strip()
            if line == "# === LEXER ===":
                in_lexer = True
                continue
            if in_lexer and line and not line.startswith("#"):
                lexer_lines.append(line)
        return lexer_lines


# ----------- Grammar class -------------
class Grammar:
    def __init__(self, grammar_text):
        self.start_symbol = ''
        self.non_terminals = set()
        self.terminals = set()
        self.productions = defaultdict(list)
        self._parse_grammar(grammar_text)

    def _parse_grammar(self, text):
        lines = text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith('START'):
                self.start_symbol = line.split('=', 1)[1].strip()
            elif line.startswith('NON_TERMINALS'):
                symbols = line.split('=', 1)[1].strip()
                self.non_terminals = set(s.strip() for s in symbols.split(',') if s.strip())
            elif line.startswith('TERMINALS'):
                symbols = line.split('=', 1)[1].strip()
                self.terminals = set(s.strip() for s in symbols.split(',') if s.strip())
            elif '->' in line:
                left, right = map(str.strip, line.split('->', 1))
                alternatives = [alt.strip() for alt in re.split(r'\s*\|\s*', right)]
                for alt in alternatives:
                    self.productions[left].append(alt)

        # اضافه کردن تمام non-terminals به مجموعه
        for head in self.productions.keys():
            self.non_terminals.add(head)

    def display(self):
        print('Start Symbol:', self.start_symbol)
        print('Non_Terminals:', self.non_terminals)
        print('Terminals:', self.terminals)
        print('Productions:')
        for head, bodies in self.productions.items():
            for body in bodies:
                print(f' {head} -> {body}')


class LL1Helper:
    def __init__(self, grammar):
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
                        sym = symbols[i]
                        if sym in self.grammar.terminals:
                            if sym not in self.first[head]:
                                self.first[head].add(sym)
                                changed = True
                            nullable = False
                        elif sym in self.grammar.non_terminals:
                            before = len(self.first[head])
                            self.first[head].update(self.first[sym] - {'eps'})
                            if 'eps' in self.first[sym]:
                                nullable = True
                            else:
                                nullable = False
                            if len(self.first[head]) > before:
                                changed = True
                        elif sym == 'eps':
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
                            beta = symbols[i+1:] if i+1 < len(symbols) else []
                            follow_before = len(self.follow[B])
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
        for sym in symbols:
            if sym in self.grammar.terminals:
                result.add(sym)
                break
            elif sym in self.grammar.non_terminals:
                result.update(self.first[sym] - {'eps'})
                if 'eps' not in self.first[sym]:
                    break
            elif sym == 'eps':
                result.add('eps')
                break
        else:
            result.add('eps')
        return result

    def display_first(self):
        print("\nFirst sets:")
        for sym, s in self.first.items():
            print(f"First({sym}) = {{ {', '.join(sorted(s))} }}")

    def display_follow(self):
        print("\nFollow sets:")
        for sym, s in self.follow.items():
            print(f"Follow({sym}) = {{ {', '.join(sorted(s))} }}")


class LL1ParsingTable:
    def __init__(self, grammar: Grammar, first_sets, follow_sets):
        self.grammar = grammar
        self.first = first_sets
        self.follow = follow_sets
        self.table = defaultdict(dict)
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

    def display(self):
        print("LL(1) Parsing Table:")
        for non_terminal in sorted(self.table.keys()):
            for terminal in sorted(self.table[non_terminal].keys()):
                production = self.table[non_terminal][terminal]
                print(f"  M[{non_terminal}, {terminal}] = {non_terminal} -> {production}")

    def _first_of_string(self, symbols):
        result = set()
        for sym in symbols:
            if sym in self.grammar.terminals:
                result.add(sym)
                break
            elif sym in self.grammar.non_terminals:
                result.update(self.first[sym] - {'eps'})
                if 'eps' not in self.first[sym]:
                    break
            elif sym == 'eps':
                result.add('eps')
                break
        else:
            result.add('eps')
        return result

    def get_table(self):
        return {(nt, t): f"{nt} -> {body}" for nt in self.table for t, body in self.table[nt].items()}


class ParseTreeNode:
    def __init__(self, symbol, value=None):
        self.symbol = symbol
        self.value = value
        self.children = []

    def display(self, level=0):
        print('  ' * level + f"{self.symbol}" + (f": {self.value}" if self.value else ""))
        for child in self.children:
            child.display(level + 1)


class DPDAParser:
    def __init__(self, grammar, parse_table):
        self.grammar = grammar
        self.parse_table = parse_table

    def parse_with_tree(self, tokens):
        stack = [('$', None)]
        stack.append((self.grammar.start_symbol, None))
        input_tokens = tokens + [('$', None)]
        index = 0
        root = None

        while stack:
            top_symbol, parent_node = stack.pop()
            current_token, current_value = input_tokens[index]
            if top_symbol == current_token:
                index += 1
                leaf = ParseTreeNode(current_token, current_value)
                if parent_node:
                    parent_node.children.append(leaf)
                continue
            elif top_symbol in self.grammar.terminals:
                return None
            key = (top_symbol, current_token)
            if key not in self.parse_table:
                return None
            rule = self.parse_table[key]
            _, rhs = rule.split('->')
            rhs_symbols = rhs.strip().split()
            node = ParseTreeNode(top_symbol)
            if parent_node:
                parent_node.children.append(node)
            else:
                root = node
            if rhs_symbols != ['eps']:
                for sym in reversed(rhs_symbols):
                    stack.append((sym, node))
        if index == len(input_tokens):
            return root
        return None


class ConfigurableLexer:
    def __init__(self, token_specs):
        self.token_specs = token_specs
        parts = [f'(?P<{name}>{pattern})' for name, pattern in self.token_specs]
        self.regex = re.compile('|'.join(parts))

    def tokenize(self, code):
        tokens = []
        for match in self.regex.finditer(code):
            kind = match.lastgroup
            value = match.group()
            if kind == 'SKIP':
                continue
            tokens.append((kind, value))
        return tokens


from graphviz import Digraph
# from parser.dpda_parser import ParseTreeNode  # توجه: قبلاً تعریف شده؛ این خط حذف شد

class ParseTreeVisualizer:
    def __init__(self):
        self.graph = Digraph(format='png')
        self.node_count = 0

    def _add_node(self, node):
        self.node_count += 1
        node_id = f"node{self.node_count}"
        label = node.symbol
        if node.value is not None:
            label += f"\n{node.value}"
        self.graph.node(node_id, label)
        return node_id

    def _build_graph(self, node, parent_id=None):
        current_id = self._add_node(node)
        if parent_id:
            self.graph.edge(parent_id, current_id)
        for child in node.children:
            self._build_graph(child, current_id)

    def render(self, root: ParseTreeNode, filename="parse_tree"):
        self.node_count = 0
        self.graph.clear()
        self._build_graph(root)
        self.graph.render(filename, view=True)


# ----------- Utility functions -------------
# (توجه: توابع استخراج بخش‌ها الان داخل SpecParser هستند، اینها رو نگه نداشتم)


def parse_grammar(grammar_text):
    """
    Create a Grammar object from grammar text.
    """
    return Grammar(grammar_text)


def parse_lexer(lexer_text):
    """
    Create a ConfigurableLexer object from lexer text.
    """
    lexer_rules = []
    for line in lexer_text.splitlines():
        if '->' in line:
            name, pattern = map(str.strip, line.split('->'))
            if pattern.startswith('/') and pattern.endswith('/'):
                pattern = pattern[1:-1]
            lexer_rules.append((name, pattern))
    return ConfigurableLexer(lexer_rules)


# ----------- Main Program -------------

def main():
    try:
        # گام 1: بارگیری فایل spec
        spec_path = input("Enter spec file path: ").strip().strip('"')
        parser = SpecParser(spec_path)
        parser.load_spec()
        parser.extract_sections()
        parser.clean_lexer()

        # گام 2: استخراج بخش‌های دستور زبان و lexer
        grammar_text = "\n".join(parser.get_grammar())
        lexer_text = "\n".join(parser.get_lexer())


        # گام 3: ساخت Grammar و Lexer
        grammar = parse_grammar(grammar_text)
        lexer = parse_lexer(lexer_text)

        # گام 4: محاسبه First و Follow و ساخت جدول LL(1)
        helper = LL1Helper(grammar)
        table = LL1ParsingTable(grammar, helper.first, helper.follow)

        print("\nFirst sets:")
        helper.display_first()
        print("\nFollow sets:")
        helper.display_follow()
        print("\nLL(1) Parsing Table:")
        table.display()

        # گام 5: گرفتن کد ورودی برای تجزیه
        print("Enter code to parse (end with empty line):")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)

        code = "\n".join(lines)

        if not code:
            print("[INFO] No input code provided. Exiting.")
            return

        # گام 6: tokenize کردن ورودی
        tokens = lexer.tokenize(code)

        # فیلتر کردن توکن‌های WHITESPACE
        tokens = [t for t in tokens if t[0] != 'WHITESPACE']

        print("\nTokens:", tokens)


        # گام 7: تجزیه کردن ورودی و ساخت درخت پارس
        dpda_parser = DPDAParser(grammar, table.get_table())
        parse_tree = dpda_parser.parse_with_tree(tokens)

        if parse_tree:
            print("\nParse Tree:")
            parse_tree.display()

            # گام 8: نمایش گرافیکی درخت پارس
            visualizer = ParseTreeVisualizer()
            visualizer.render(parse_tree, "parse_tree")
            print("[INFO] Parse tree image generated as 'parse_tree.png'.")
        else:
            print("[ERROR] Parsing failed.")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
