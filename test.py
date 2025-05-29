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

    def display(self):
        print("\nLL1 Parsing Table:")
        for non_terminal in self.grammar.non_terminals:
            for terminal in self.grammar.terminals.union({'$'}):
                if terminal in self.table[non_terminal]:
                    production = self.table[non_terminal][terminal]
                    print(f"M[{non_terminal}, {terminal}] = {non_terminal} -> {production}")





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

g = Grammar(grammar_text)
helper = LL1Helper(g)
ll1_table = LL1ParsingTable(g, helper.first, helper.follow)
ll1_table.display()

