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

from qiskit_aqua.algorithms.components.optimizers import Optimizer
from ._nloptimizer import minimize
import importlib
import logging

try:
    import nlopt
except ImportError:
    raise ImportWarning('nlopt cannot be imported')

logger = logging.getLogger(__name__)


class ISRES(Optimizer):
    """ISRES (Improved Stochastic Ranking Evolution Strategy).

    NLopt global optimizer, derivative-free
    http://nlopt.readthedocs.io/en/latest/NLopt_Algorithms/#isres-improved-stochastic-ranking-evolution-strategy
    """
    CONFIGURATION = {
        'name': 'ISRES',
        'description': 'GN_ISRES Optimizer',
        'input_schema': {
            '$schema': 'http://json-schema.org/schema#',
            'id': 'isres_schema',
            'type': 'object',
            'properties': {
                'max_evals': {
                    'type': 'integer',
                    'default': 1000
                }
            },
            'additionalProperties': False
        },
        'support_level': {
            'gradient': Optimizer.SupportLevel.ignored,
            'bounds': Optimizer.SupportLevel.supported,
            'initial_point': Optimizer.SupportLevel.required
        },
        'options': ['max_evals'],
        'optimizer': ['global']
    }

    def __init__(self):
        super().__init__()

    @staticmethod
    def check_pluggable_valid():
        try:
            spec = importlib.util.find_spec('nlopt')
            if spec is not None:
                return True
        except:
            pass

        logger.info("nlopt is not installed. Please install it if you want to use them.")
        return False

    def optimize(self, num_vars, objective_function, gradient_function=None,
                 variable_bounds=None, initial_point=None):
        super().optimize(num_vars, objective_function, gradient_function, variable_bounds, initial_point)

        return minimize(nlopt.GN_ISRES, objective_function, variable_bounds, initial_point, **self._options)
