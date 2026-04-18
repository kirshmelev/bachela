import networkx as nx

# Совместимость старой bpmn_python с новым networkx
def patch_networkx_for_bpmn_python():
    graph_types = [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]

    for graph_type in graph_types:
        if not hasattr(graph_type, "node"):
            graph_type.node = property(lambda self: self._node)

        if not hasattr(graph_type, "edge"):
            graph_type.edge = property(lambda self: self._adj)


patch_networkx_for_bpmn_python()

from bpmn_python.bpmn_diagram_rep import BpmnDiagramGraph
from bpmn_python.bpmn_diagram_import import BpmnDiagramGraphImport
from bpmn_python import bpmn_diagram_visualizer


def convert_bpmn_to_png(input_file: str = "a.xml", output_file: str = "diagram.png"):
    print(f"Загружаю BPMN XML из файла: {input_file}")

    bpmn_graph = BpmnDiagramGraph()

    BpmnDiagramGraphImport.load_diagram_from_xml(input_file, bpmn_graph)

    print("Импорт завершён. Генерирую PNG...")

    bpmn_diagram_visualizer.bpmn_diagram_to_png(bpmn_graph, output_file)

    print(f"Готово: {output_file}")


if __name__ == "__main__":
    convert_bpmn_to_png()