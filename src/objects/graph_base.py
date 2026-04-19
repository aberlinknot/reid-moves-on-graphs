"""
Base graph class wrapping networkx.Graph for custom methods and extensions.

All code, comments, and docstrings must be in English (NumPy style).
"""

from collections.abc import Hashable, Iterable
import networkx as nx

type Node = Hashable
type Edge = tuple[Node, Node]

class BaseGraph:
    """
    Base class for graphs, extending networkx.Graph with custom methods.

    Parameters
    ----------
    data : Iterable[Edge] | None
        Initial edges for the graph.
    **attr : object
        Additional attributes for the graph.
    """

    def __init__(self, data: Iterable[Edge] | None = None, **attr: object) -> None:
        self.nx_graph: nx.Graph = nx.Graph(data, **attr)

    @classmethod
    def from_networkx(cls, graph: nx.Graph) -> "BaseGraph":
        """
        Build BaseGraph from an existing networkx.Graph.

        Parameters
        ----------
        graph : nx.Graph
            Source graph.

        Returns
        -------
        BaseGraph
            New wrapper over a copied source graph.
        """
        instance = cls()
        instance.nx_graph = graph.copy()
        return instance

    def copy(self) -> "BaseGraph":
        """Return a deep copy of the wrapped graph object."""
        return BaseGraph.from_networkx(self.nx_graph)

    def add_node(self, node: Node, **attr: object) -> None:
        """Add a single node to the graph."""
        self.nx_graph.add_node(node, **attr)

    def add_edge(self, u: Node, v: Node, **attr: object) -> None:
        """Add an edge between nodes u and v."""
        self.nx_graph.add_edge(u, v, **attr)

    def nodes(self) -> list[Node]:
        """Return graph nodes as a list."""
        return list(self.nx_graph.nodes)

    def edges(self) -> list[Edge]:
        """Return graph edges as a list of node pairs."""
        return list(self.nx_graph.edges)

    def to_networkx(self) -> nx.Graph:
        """Return the underlying networkx.Graph object."""
        return self.nx_graph
