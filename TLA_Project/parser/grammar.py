from collections import defaultdict

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
                self.start_symbol = line.split('=')[1].strip()
            elif line.startswith('NON_TERMINALS'):
                symbols = line.split('=')[1].strip()
                self.non_terminals = set(s.strip() for s in symbols.split(','))
            elif line.startswith('TERMINALS'):
                symbols = line.split('=')[1].strip()
                self.terminals = set(s.strip() for s in symbols.split(','))
            elif '->' in line:
                left, right = map(str.strip, line.split('->', 1))
                alternatives = [alt.strip() for alt in right.split('|')]
                for alt in alternatives:
                    self.productions[left].append(alt)