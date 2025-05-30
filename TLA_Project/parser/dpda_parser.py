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
