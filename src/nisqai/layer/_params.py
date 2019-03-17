#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from itertools import chain

from pyquil.quil import Program


# Standard specification format for strings.
# Fill character: 0
# Right justified: >
# Three digits long: 3
FORMAT_SPEC = "0>3"

# TODO: tasks left to do for Parameters class.
# TODO: (1) Add method for removing parameters.
# TODO: (2) Add method for adding parameters.
# TODO: (3) Add method for simplifying parameters (e.g., all product ansatz parameters are equal).
# TODO: (4) Add method for removing parameters from a particular qubit.
# TODO: (5) Etc. Any other methods that would be useful.


class Parameters:
    """Efficient data structure for storing and working with parameters in an ansatz.

    Key attributes:

        (1) Parameters.list_values
            One dimensional list of parameter values for use in training.

        (2) Parameters.grid_values
            Two dimensional array of parameter values for efficient placement
            and visualization.

        (3) Parameters.memory_map
            Dictionary of {parameter name: parameter value} pairs for use in
            parameteric compilation.
    """

    def __init__(self, parameters):
        """Initializes a Parameters class.

        Args:
            parameters : dict[int, list[float]]
                Dictionary of

                {qubit : list of parameter values for qubit}

                pairs.

                IMPORTANT: All qubit indices must explicitly be included as keys, even if
                some qubits do not have parameterized gates.

                Qubits with no parameterized gates should have empty lists as values
                for that qubit index.

                Examples:

                    parameters = {0 : [1, 2],
                                  1 : [3, 4]}

                        Corresponds to a circuit which looks like:

                        Qubit 0 ----[1]----[2]----
                        Qubit 1 ----[3]----[4]----

                        That is: A circuit with two qubits, 0 and 1, where qubit 0 has
                        parameters 1 and 2 for its first and second parameterized gates,
                        respectively, and qubit 1 has parameters 3 and 4 for its first
                        and second parameterized gates, respectively.

                        Note that other unparameterized gates can appear in the circuit,
                        at any point before, in between, or after parameterized gates.



                    parameters = {0 : [1, 2],
                                  1 : []
                                  2 : [3]}

                        Corresponds to a circuit which looks like:

                        Qubit 0 ----[1]----[2]----
                        Qubit 1 ------------------
                        Qubit 2 ----[3]-----------

                    That is: A circuit with three qubits. Qubit 0 has parameters 1 and 2
                    for its first and second parameterized gates, respectively. Qubit 1
                    has no parameterized gates. Qubit 2 has parameter 3 for its first
                    parameterized gate.
        """
        # store the parameter dictionary
        # TODO: write a method to make sure the parameter dictionary is valid
        self._values = parameters

        # extract the number of qubits
        self._num_qubits = len(self._values.keys())

        # make the dictionary of parameter names
        self.names = self._make_parameter_names()

    def _make_parameter_names(self):
        """Returns a dictionary of names according to the standard naming convention.

        The standard naming convention is given by

        q_ABC_g_XYZ

        where

        ABC = three digit integer label of qubit

        and

        XYZ = three digit integer label of gate.

        Examples:
            q_000_g_005 = Fifth parameterized gate on qubit zero.
            q_999_g_024 = Twenty fourth (!) parameterized gate on qubit 999. (!!!)
        """
        names = {}
        for qubit in self._values.keys():
            names[qubit] = []
            qubit_key = format(qubit, FORMAT_SPEC)
            for gate in range(len(self._values[qubit])):
                gate_key = format(gate, FORMAT_SPEC)
                names[qubit].append(
                    "q_{}_g_{}".format(qubit_key, gate_key)
                )
        return names

    @property
    def values(self):
        """Returns the current values of the Parameters as a dict."""
        return self._values

    def list_values(self):
        """Returns a one dimensional list of all parameter values."""
        return list(chain.from_iterable(self._values.values()))

    def list_names(self):
        """Returns a one dimensional list of all parameter names."""
        return list(chain.from_iterable(self.names.values()))

    def grid_values(self):
        """Returns a two dimensional array of all parameter values."""
        return list(self._values.values())

    def grid_names(self):
        """Returns a two dimensional array of all parameter names."""
        return list(self.names.values())

    def memory_map(self):
        """Returns a memory map for use in pyQuil.

        A memory map is defined by a dictionary of

        {parameter name: parameter value}

        pairs.
        """
        # TODO: speedup implementation of this method: crucial for fast implementations
        # TODO: make more Pythonic
        mem_map = {}
        for qubit in range(len(self._values)):
            for gate in range(len(self._values[qubit])):
                mem_map[self.names[qubit][gate]] = [float(self._values[qubit][gate])]
        return mem_map

    def update_values(self, values):
        """Updates the values of the Parameters in place."""
        self._values = values

    def update_values_memory_map(self, values):
        """Updates the values of the parameters in place and returns a memory map."""
        self._values = values
        return self.memory_map()

    def depth(self):
        """Returns the depth of the Parameters, defined as the maximum length
        of all parameter lists over all qubits.
        """
        return len(max(self._values.values(), key=len))

    def shape(self):
        """Returns the (height, width) of a quantum circuit, where:

        height = number of qubits
        width  = depth of the Parameters

        Note that some qubits may have fewer parameters than the width.

        Return type: Tuple
        """
        return self._num_qubits, self.depth()

    def declare_memory_references(self, program):
        """Declares all Parameters in a pyQuil Program.

        Args:
            program : pyquil.Program
                The program to declare parameters for.
            """
        # error checks
        if type(program) != Program:
            raise ValueError("Argument program must be a pyquil.Program.")

        # dictionary to store memory references
        mem_refs = {}

        # loop through all circuit locations and create memory references
        for qubit in range(len(self.names)):
            # create empty list to append memory references to
            mem_refs[qubit] = []
            for name in self.names[qubit]:
                mem_ref = program.declare(
                    name, memory_type="REAL", memory_size=1
                )
                mem_refs[qubit].append(mem_ref)

        # TODO: should Parameters input a circuit/ansatz?
        self.memory_references = mem_refs


def product_ansatz_parameters(num_qubits, depth, value):
    """Returns Parameters for a product ansatz on the given
    number of qubits for the input depth.

    Args:
        num_qubits : int
            Number of qubits in the ansatz.

        depth : int
            Number of parameterized gates appearing on each qubit.

        value : Union[float, int]
            Initial parameter value that appears in all gates.
    """
    # error checks
    if type(num_qubits) != int:
        raise ValueError("num_qubits must be an integer.")
    if type(depth) != int:
        raise ValueError("depth must be an integer.")
    try:
        value = float(value)
    except TypeError:
        print("Invalid type for value.")
        raise TypeError

    # dictionary to store parameter values
    params = {}

    # fill the dictionary with the initial parameter
    for qubit in range(num_qubits):
        params[qubit] = [value] * depth

    # return the Parameters
    return Parameters(params)
