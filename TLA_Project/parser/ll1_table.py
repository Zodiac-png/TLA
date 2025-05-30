from parser.grammar import Grammar
from collections import defaultdict

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
            print(f"First({sym}) = {{ {', '.join(s)} }}")

    def display_follow(self):
        print("\nFollow sets:")
        for sym, s in self.follow.items():
            print(f"Follow({sym}) = {{ {', '.join(s)} }}")

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