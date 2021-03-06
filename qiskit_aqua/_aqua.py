# -*- coding: utf-8 -*-

# Copyright 2018 IBM.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

"""Algorithm functions for running etc."""

import copy
import json
import logging

from qiskit.backends import BaseBackend

from qiskit_aqua.aqua_error import AquaError
from qiskit_aqua._discover import (_discover_on_demand,
                                   local_pluggables,
                                   PluggableType,
                                   get_pluggable_class)
from qiskit_aqua.utils.jsonutils import convert_dict_to_json, convert_json_to_dict
from qiskit_aqua.parser._inputparser import InputParser
from qiskit_aqua.parser import JSONSchema

logger = logging.getLogger(__name__)


def run_algorithm(params, algo_input=None, json_output=False, backend=None):
    """
    Run algorithm as named in params, using params and algo_input as input data
    and returning a result dictionary

    Args:
        params (dict): Dictionary of params for algo and dependent objects
        algo_input (AlgorithmInput): Main input data for algorithm. Optional, an algo may run entirely from params
        json_output (bool): False for regular python dictionary return, True for json conversion
        backend (BaseBackend): Backend object to be used in place of backend name

    Returns:
        Result dictionary containing result of algorithm computation
    """
    _discover_on_demand()

    inputparser = InputParser(params)
    inputparser.parse()
    inputparser.validate_merge_defaults()
    logger.debug('Algorithm Input: {}'.format(json.dumps(inputparser.get_sections(), sort_keys=True, indent=4)))

    algo_name = inputparser.get_section_property(PluggableType.ALGORITHM.value, JSONSchema.NAME)
    if algo_name is None:
        raise AquaError('Missing algorithm name')

    if algo_name not in local_pluggables(PluggableType.ALGORITHM):
        raise AquaError('Algorithm "{0}" missing in local algorithms'.format(algo_name))

    backend_cfg = None
    backend_name = inputparser.get_section_property(JSONSchema.BACKEND, JSONSchema.NAME)
    if backend_name is not None:
        backend_cfg = {k: v for k, v in inputparser.get_section(JSONSchema.BACKEND).items() if k != 'name'}
        backend_cfg['backend'] = backend_name

    if backend is not None and isinstance(backend, BaseBackend):
        if backend_cfg is None:
            backend_cfg = {}

        backend_cfg['backend'] = backend

    if algo_input is None:
        input_name = inputparser.get_section_property('input', JSONSchema.NAME)
        if input_name is not None:
            input_params = copy.deepcopy(inputparser.get_section_properties('input'))
            del input_params[JSONSchema.NAME]
            convert_json_to_dict(input_params)
            algo_input = get_pluggable_class(PluggableType.INPUT, input_name).from_params(input_params)

    algo_params = copy.deepcopy(inputparser.get_sections())
    algorithm = get_pluggable_class(PluggableType.ALGORITHM,
                                    algo_name).init_params(algo_params, algo_input)
    algorithm.random_seed = inputparser.get_section_property(JSONSchema.PROBLEM, 'random_seed')
    if backend_cfg is not None:
        algorithm.setup_quantum_backend(**backend_cfg)

    value = algorithm.run()
    if isinstance(value, dict) and json_output:
        convert_dict_to_json(value)

    return value


def run_algorithm_to_json(params, algo_input=None, jsonfile='algorithm.json'):
    """
    Run algorithm as named in params, using params and algo_input as input data
    and save the combined input as a json file. This json is self-contained and
    can later be used as a basis to call run_algorithm

    Args:
        params (dict): Dictionary of params for algo and dependent objects
        algo_input (AlgorithmInput): Main input data for algorithm. Optional, an algo may run entirely from params
        jsonfile (str): Name of file in which json should be saved

    Returns:
        Result dictionary containing the jsonfile name
    """
    _discover_on_demand()

    inputparser = InputParser(params)
    inputparser.parse()
    inputparser.validate_merge_defaults()

    algo_params = copy.deepcopy(inputparser.get_sections())

    if algo_input is not None:
        input_params = algo_input.to_params()
        convert_dict_to_json(input_params)
        algo_params['input'] = input_params
        algo_params['input']['name'] = algo_input.configuration['name']

    logger.debug('Result: {}'.format(json.dumps(algo_params, sort_keys=True, indent=4)))
    with open(jsonfile, 'w') as fp:
        json.dump(algo_params, fp, sort_keys=True, indent=4)

    logger.info("Algorithm input file saved: '{}'".format(jsonfile))

    return {'jsonfile': jsonfile}
