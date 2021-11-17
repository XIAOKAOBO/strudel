#!/usr/bin/env python3
import argparse
import logging
import os.path
from timeit import default_timer

# from create_database import load
from pebble import ProcessPool

from cstrudel import cstrudel
# from evaluation import collect_expr_results
from lstrudel import LStrudel, create_line_feature_vector
from src import lstrudel
from src.classification import CrossValidation
from src.data import load_data
from src.utility import process_pebble_results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Argument parser for line & cell classification script.')
    parser.add_argument('-d', default='all', help="Specify the training dataset. Default 'all' uses all data-sets.")
    parser.add_argument('-t', help='Specify the test dataset. If not given, apply cross-validation on the training dataset.')
    parser.add_argument('-a', default='l2c', help='Specify which algorithm_package to run.')
    parser.add_argument('-c', default='all', help='The tested component for cstrudel.')
    parser.add_argument('-p', default=False, type=bool, help='Populating the database with data files. Default is false.')
    parser.add_argument('-f', default='../data/', help='Path of the data files to be populated into the database.')
    parser.add_argument('-v', default='../feature_vec/', help='Path of feature vectors.')
    parser.add_argument('-o', default='../result/', help='Path where all experiment result files are stored.')
    parser.add_argument('-para', help='The parameters used for the specified algorithm_package.')
    parser.add_argument('-ms', default=False, type=bool, help='Whether using model selection approach to select the best hyperparameters for the model.')
    parser.add_argument('-i', default=0, type=int, help='The number of this iteration.')

    args = parser.parse_args()
    print(args)

    training_dataset = args.d
    test_dataset = args.t
    algorithm_name = args.a
    cstrudel_component = args.c
    is_populate = args.p
    data_file_path = args.f
    feature_vector_path = args.v
    output_path = str(args.o)
    parameters = args.para
    n_iter = str(args.i)

    max_workers = int(os.cpu_count() * 0.5)
    max_tasks = 10

    runtime = 0
    true_labels = None
    pred_labels = None
    algorithm_type = None
    description = None

    if test_dataset is None:
        dataset_path = os.path.join(data_file_path, training_dataset + '.jl.gz')
        dataset = load_data(dataset_path=dataset_path)

        with ProcessPool(max_workers=max_workers, max_tasks=max_tasks) as pool:
            optional_line_feature_vectors = pool.map(create_line_feature_vector, dataset).result()

        line_fvs_dataset = process_pebble_results(optional_line_feature_vectors)

        cv = CrossValidation(n_splits=2)
        cv.cross_validate(line_fvs_dataset)

    if algorithm_name == 'cstrudel':
        algorithm_type = 'cell'
        algorithm = cstrudel(data_file_path, training_dataset, feature_vector_path, cstrudel_component)
        true_labels, pred_labels = algorithm.run()
        result = algorithm.result
        result_output_path = output_path + training_dataset + '/' + 'result_' + n_iter + '.csv'
        result.to_csv(result_output_path, index=False)
        description = cstrudel_component
        runtime = algorithm.runtime

    print(runtime)

    # collect_expr_results(true_labels, pred_labels, algorithm_name, algorithm_type, dataset_name, runtime, description)
