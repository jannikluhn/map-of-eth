DEFAULT_NODE_ATTRS = {
    "label": "",
    "shape": "circle",
}


def store_graph(nodes, edges, f):
    f.write("strict graph {\n")
    for n, attrs in nodes.items():
        attrs = {
            **DEFAULT_NODE_ATTRS,
            **attrs,
        }
        f.write(f'"{n}" {stringify_attrs(attrs)};\n')
    for (n1, n2), attrs in edges.items():
        f.write(f'"{n1}" -- "{n2}"  {stringify_attrs(attrs)};\n')
    f.write("}")


def stringify_attrs(attrs):
    attrs_strings = [f'{k}="{v}"' for k, v in attrs.items()]
    return "[" + ", ".join(attrs_strings) + "]"
