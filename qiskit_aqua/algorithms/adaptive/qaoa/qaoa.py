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


import logging

from qiskit_aqua import QuantumAlgorithm, AquaError, PluggableType, get_pluggable_class
from qiskit_aqua.algorithms.adaptive import VQE
from .varform import QAOAVarForm

logger = logging.getLogger(__name__)


class QAOA(VQE):
    """
    The Quantum Approximate Optimization Algorithm.

    See https://arxiv.org/abs/1411.4028
    """

    CONFIGURATION = {
        'name': 'QAOA.Variational',
        'description': 'Quantum Approximate Optimization Algorithm',
        'input_schema': {
            '$schema': 'http://json-schema.org/schema#',
            'id': 'qaoa_schema',
            'type': 'object',
            'properties': {
                'operator_mode': {
                    'type': 'string',
                    'default': 'matrix',
                    'oneOf': [
                        {'enum': ['matrix', 'paulis', 'grouped_paulis']}
                    ]
                },
                'p': {
                    'type': 'integer',
                    'default': 1,
                    'minimum': 1
                },
                'initial_point': {
                    'type': ['array', 'null'],
                    "items": {
                        "type": "number"
                    },
                    'default': None
                },
                'batch_mode': {
                    'type': 'boolean',
                    'default': False
                }
            },
            'additionalProperties': False
        },
        'problems': ['ising'],
        'depends': ['optimizer'],
        'defaults': {
            'optimizer': {
                'name': 'COBYLA'
            },
        }
    }

    def __init__(self, operator, optimizer, p=1, operator_mode='matrix', initial_point=None,
                 batch_mode=False, aux_operators=None):
        """
        Args:
            operator (Operator): Qubit operator
            operator_mode (str): operator mode, used for eval of operator
            p (int) : the integer parameter p as specified in https://arxiv.org/abs/1411.4028
            optimizer (Optimizer) : the classical optimization algorithm.
            initial_point (str) : optimizer initial point.
        """
        self.validate(locals())
        var_form = QAOAVarForm(operator, p)
        super().__init__(operator, var_form, optimizer,
                         operator_mode=operator_mode, initial_point=initial_point)

    @classmethod
    def init_params(cls, params, algo_input):
        """
        Initialize via parameters dictionary and algorithm input instance

        Args:
            params (dict): parameters dictionary
            algo_input (EnergyInput): EnergyInput instance
        """
        if algo_input is None:
            raise AquaError("EnergyInput instance is required.")

        operator = algo_input.qubit_op

        qaoa_params = params.get(QuantumAlgorithm.SECTION_KEY_ALGORITHM)
        operator_mode = qaoa_params.get('operator_mode')
        p = qaoa_params.get('p')
        initial_point = qaoa_params.get('initial_point')
        batch_mode = qaoa_params.get('batch_mode')

        # Set up optimizer
        opt_params = params.get(QuantumAlgorithm.SECTION_KEY_OPTIMIZER)
        optimizer = get_pluggable_class(PluggableType.OPTIMIZER,
                                        opt_params['name']).init_params(opt_params)

        return cls(operator, optimizer, p=p, operator_mode=operator_mode,
                   initial_point=initial_point, batch_mode=batch_mode,
                   aux_operators=algo_input.aux_ops)
