import json
import pathlib

import ifcopenshell
import topologic_core
from topologicpy.Cell import Cell
from topologicpy.Cluster import Cluster
from topologicpy.Dictionary import Dictionary
from topologicpy.Topology import Topology

def get_ifc_metadata_from_cell(cell: Cell) -> dict:
    metadata = {}
    dictionary = cell.GetDictionary()
    keys = dictionary.Keys()
    for key in keys:
        try:
            attr = dictionary.ValueAtKey(key)
        except:
            raise Exception("Dictionary.Values - Error: Could not retrieve a Value at the specified key (" + key + ")")
        if isinstance(attr, topologic_core.IntAttribute):  # Hook to Core
            metadata[key] = attr.IntValue()
        elif isinstance(attr, topologic_core.DoubleAttribute):  # Hook to Core
            metadata[key] = attr.DoubleValue()
        elif isinstance(attr, topologic_core.StringAttribute):  # Hook to Core
            temp_str = attr.StringValue()
            if temp_str.startswith("{") and temp_str.endswith("}"):
                metadata[key] = json.loads(temp_str)
            elif temp_str == "__NONE__":
                metadata[key] = None
            else:
                metadata[key] = temp_str
        elif isinstance(attr, topologic_core.ListAttribute):  # Hook to Core
            metadata[key] = Dictionary.ListAttributeValues(attr)
        else:
            metadata[key] = ""

    return metadata

def test_by_ifc_cell_complex():
    result = Topology.ByIFCFile(ifcopenshell.open(pathlib.Path(__file__).parent.parent / "resources/dev_topo_concept.ifc"),
                                removeCoplanarFaces=True, transferDictionaries=True)
    topologies = list(filter(lambda x: x is not None, result))

    if not isinstance(topologies, list):
        raise ValueError(
            "Topology.MergeAll - Error: the input topologies parameter is not a valid list. Returning None."
        )
    other = []
    equipments = []
    topologies_filtered = []
    for t in topologies:
        if not Topology.IsInstance(t, "Topology"):
            continue
        meta = get_ifc_metadata_from_cell(t)
        ifc_function = meta.get("IFC_Properties", {}).get("IFC_function")
        if ifc_function is None:
            continue
        if ifc_function == "equipment":
            equipments.append(t)
        elif ifc_function == "space":
            topologies_filtered.append(t)
        else:
            other.append((ifc_function, t))

    if len(topologies_filtered) < 1:
        raise ValueError(
            "Topology.MergeAll - Error: the input topologyList does not contain any valid topologies. Returning None."
        )
    print(len(topologies_filtered), "spaces found.")
    cluster = Cluster.ByTopologies(topologies_filtered, transferDictionaries=True)
    cells = Topology.Cells(cluster)
    print(f"cluster {cells=}")
    cell_complex = Topology.SelfMerge(cluster, transferDictionaries=True)
    cells = Topology.Cells(cell_complex)
    print(f"cell_complex {cells=}")
    if not isinstance(cell_complex, topologic_core.CellComplex):
        raise ValueError("Topology.MergeAll - Error: the output cellComplex is not a valid CellComplex.")

    print("CellComplex created successfully.")