from graphviz import Digraph
from parser.dpda_parser import ParseTreeNode
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
