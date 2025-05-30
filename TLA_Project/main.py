from lexer.lexer import Lexer
from parser.grammar import Grammar
from parser.ll1_table import LL1ParsingTable, LL1Helper
from parser.dpda_parser import DPDAParser
from visualizer.tree_visualizer import ParseTreeVisualizer

def main():
    grammar_file = input("Enter grammar file path (e.g., grammars/expr_grammar.txt): ").strip()
    
    print("Enter code to parse (end with an empty line):")
    lines = []
    while True:
        line = input()
        if line.strip() == '':
            break
        lines.append(line)
    code = '\n'.join(lines)

    # بارگذاری گرامر
    with open(grammar_file, 'r') as f:
        grammar_text = f.read()

    grammar = Grammar(grammar_text)
    helper = LL1Helper(grammar)
    table = LL1ParsingTable(grammar, helper.first, helper.follow)
    parse_table = table.get_table()

    # توکنایز کردن کد
    lexer = Lexer()
    try:
        tokens = lexer.tokenize(code)
    except RuntimeError as e:
        print(f"Lexer error: {e}")
        return

    print("Tokens:", tokens)

    # پارس کردن
    parser = DPDAParser(grammar, parse_table)
    tree = parser.parse_with_tree(tokens)

    if tree:
        print("\nParse Tree:")
        tree.display()

        visualizer = ParseTreeVisualizer()
        visualizer.render(tree, "parse_tree")
    else:
        print("❌ Parse error.")

        
if __name__ == '__main__':
    main()