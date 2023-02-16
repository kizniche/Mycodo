# coding=utf-8
import logging

logger = logging.getLogger("mycodo.atlas_scientific")


def constraints_pass_percent(mod_dev, value):
    """
    Check if the user input is acceptable
    :param mod_dev: SQL object with user-saved options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if 100 < value or value < 0:
        all_passed = False
        errors.append("Must be between 0 and 100")
    return all_passed, errors, mod_dev

def constraints_pass_positive_value(mod_dev, value):
    """
    Check if the user input is acceptable
    :param mod_dev: SQL object with user-saved options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_dev

def constraints_pass_positive_or_zero_value(mod_dev, value):
    """
    Check if the user input is acceptable
    :param mod_dev: SQL object with user-saved options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is above 0
    if value < 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_dev
