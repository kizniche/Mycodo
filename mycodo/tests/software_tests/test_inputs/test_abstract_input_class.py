# coding=utf-8
"""Tests for the abstract class and sensor classes."""
import pytest
from testfixtures import LogCapture

from mycodo.inputs.base_input import AbstractInput


# ----------------------------
#   AbstractInput
# ----------------------------
def test_abstract_input_get_measurement_method_logs_when_not_implemented():
    """ Verify that methods that are not overwritten log as errors."""
    with LogCapture() as log_cap:
        with pytest.raises(NotImplementedError):
            AbstractInput(None, testing=True).get_measurement()
    expected_error = ('mycodo.inputs.base_input',
                      'ERROR',
                      ('AbstractInput did not overwrite the get_measurement() '
                       'method. All subclasses of the AbstractInput '
                       'class are required to overwrite this method'))
    assert expected_error in log_cap.actual()
