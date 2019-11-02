# coding=utf-8
import logging

logger = logging.getLogger(__name__)


def get_from_db(schema, table, unique_id=None):
    table_schema = schema()
    if unique_id:
        data = return_dictionary(table_schema.dump(
            table.query.filter_by(unique_id=unique_id).first()))
    else:
        data = return_list_of_dictionaries(
            table_schema.dump(table.query.all(), many=True))
    return data


def return_list_of_dictionaries(data):
    """
    marshmallow schema dump with many=True sometimes returns a list of
    dictionaries (e.g. [{}, {}, ...]) and sometimes a list of a list of
    dictionaries (e.g. [[{}, {}, ...]]). This returns a list of dictionaries.
    """
    return_list = []
    if hasattr(data, 'data'):
        data = data.data
    if isinstance(data, list):
        return_list = data
        if len(data) > 0 and isinstance(data[0], list):
            return_list = data[0]
    if return_list is None:
        return_list = []
    return return_list


def return_dictionary(data):
    """
    marshmallow schema dump sometimes returns a list with a dictionary
    (e.g. [{}]) and sometimes just a dictionary. This returns just the
    dictionary.
    """
    return_dict = {}
    if hasattr(data, 'data'):
        data = data.data
    if isinstance(data, dict):
        return_dict = data
    elif isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            return_dict = data[0]
    return return_dict
