import re

class Lexer:
    token_specification = [
        ('FUNCTION', r'\bfunction\b'),
        ('IF', r'\bif\b'),
        ('WHILE', r'\bwhile\b'),
        ('RETURN', r'\breturn\b'),
        ('ID', r'[a-zA-Z_]\w*'),
        ('NUM', r'-?\d+(\.\d+)?([eE][+-]?\d+)?'),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('STAR', r'\*'),
        ('SLASH', r'/'),
        ('LEFT_PAR', r'\('),
        ('RIGHT_PAR', r'\)'),
        ('LEFT_BRACE', r'\{'),
        ('RIGHT_BRACE', r'\}'),
        ('EQUALS', r'='),
        ('SEMICOLON', r';'),
        ('SKIP', r'[ \t\n]+'),
        ('MISMATCH', r'.'),
    ]

    def __init__(self):
        parts = []
        for name, pattern in self.token_specification:
            parts.append(f'(?P<{name}>{pattern})')
        self.regex = re.compile('|'.join(parts))

    def tokenize(self, code):
        tokens = []
        for mo in self.regex.finditer(code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character: {value}')
            tokens.append((kind, value))
        return tokens
