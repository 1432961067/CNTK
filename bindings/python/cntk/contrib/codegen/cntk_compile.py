# ==============================================================================
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================
"""
Generator of the eval graph for a given CNTK model.
"""

from cntk import *
from cntk import cntk_py
from .util import *
from .model_transforms import *
from .expression_generator import *
import networkx as nx
import matplotlib.pyplot as plt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', help='Path to the CNTK model file',
                        required=True, default=None)
    parser.add_argument('-p', '--plot', help='Path to the output file with resulting DAG of the model. Should have one of supported suffixes (i.e. pdf)',
                        required=False, default=None)
    parser.add_argument('-c', '--classname', help='Name of the resulting class',
                        required=False, default='Evaluator')
    parser.add_argument('-o', '--output', help='File name for the output',
                        required=False, default='Evaluator.h')
    parser.add_argument('-w', '--weights', help='File name for the serialized weights/constants',
                        required=False, default='weights.json')
    args = vars(parser.parse_args())

    # Create the graph and perform some transforms on it
    model = Function.load(args['model'])
    graph = ModelToGraphConverter().convert(model)
    remove_intermediate_output_nodes(graph)
    split_past_values(graph)

    # Ok, let's plot the resulting graph if asked.
    if args['plot']:
        nx_plot(graph, args['plot'])

    if not nx.is_directed_acyclic_graph(g):
        raise ValueError('Unsupported type of graph: please make sure there are no loops or non connected components')

    # Perform topological sort for evaluation
    nodes_sorted_for_eval = nx.topological_sort(graph)

    # Now generate the actual C++ file with the evaluator inside
    listing = HalideExpressionGenerator(g).generate(nodes_sorted_for_eval, args['classname'])

    with open(args['output'], 'w') as f:
        f.write(listing)

    # Also make sure we generate the json weights/constants for now.
    # There should be taken by C++ directly from the model though.
    WeigthExtractor(graph).dump(args['weights'])