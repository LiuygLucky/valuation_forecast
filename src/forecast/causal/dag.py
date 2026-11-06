import networkx as nx


def validate_dag(config: dict):
    graph = nx.DiGraph()
    edge_ids = set()
    for edge in config["edges"]:
        if edge["id"] in edge_ids or edge["lag_days"][0] < 0:
            raise ValueError("invalid DAG edge")
        if not edge["meaning"] or not edge["parameter_source"]:
            raise ValueError("edge hypothesis and parameter provenance required")
        edge_ids.add(edge["id"])
        graph.add_edge(edge["cause"], edge["effect"], **edge)
    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("causal graph must be acyclic")
    by_id = {e["id"]: e for e in config["edges"]}
    for mechanism in config["mechanisms"].values():
        path = mechanism["path"]
        if not set(path) <= edge_ids:
            raise ValueError("unregistered path")
        for a, b in zip(path, path[1:]):
            if by_id[a]["effect"] != by_id[b]["cause"]:
                raise ValueError("disconnected mechanism path")
    return graph


def mermaid(config: dict) -> str:
    return "graph LR\n" + "\n".join(
        f"  {e['cause']} -->|{e['id']}| {e['effect']}" for e in config["edges"]
    )
