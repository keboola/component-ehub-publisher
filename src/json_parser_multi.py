from typing import Optional, List


class ParserException(Exception):
    pass


class MulitCsvJsonParser:
    def __init__(self, dont_parse_list: Optional[List]):
        self.dont_parse_list = dont_parse_list or []

    def parse_data(self, json_data, main_table_name):
        self.validate_parser_input(json_data)
        data = {}
        for row in json_data:
            parsed_row = self._parse_row_to_tables(row, main_table_name)
            for key in parsed_row:
                if key not in data:
                    data[key] = []
                data[key].extend(parsed_row[key])
        return data

    def _parse_row_to_tables(self, data_object, main_table_name):
        table_data = {main_table_name: []}

        def init_table(key):
            if key not in table_data:
                table_data[key] = []

        def parse_list(table_name, key, customer_data, current_foreign_id):
            init_table(key)
            foreign_key = f"{table_name}_id"
            for i in customer_data[key]:
                table_data[key].append({foreign_key: current_foreign_id, "value": i})

        def parse_list_of_dicts(table_name, key, customer_data, foreign_key):
            init_table(key)
            foreign_key_name = f"{table_name}_id"
            for index, d in enumerate(customer_data[key]):
                parse_nested_dict(d, key, foreign_key_name=foreign_key_name, foreign_key=foreign_key, table_index=index)

        def get_primary_key(customer_data):
            primary_key = "id"
            if "id" in customer_data:
                primary_key = customer_data["id"]
            return primary_key

        def parse_nested_dict(customer_data, table_name, foreign_key_name="", foreign_key="", table_index=0):
            primary_key = get_primary_key(customer_data)
            for index, key in enumerate(customer_data):
                type_of_var = type(customer_data[key])
                if self._is_list_of_dicts(customer_data[key]) and key not in self.dont_parse_list:
                    parse_list_of_dicts(table_name, key, customer_data, primary_key)
                elif type_of_var == dict and key not in self.dont_parse_list:
                    flatten_simple_dict(customer_data[key], table_name, table_index)
                elif type_of_var == list and key not in self.dont_parse_list:
                    parse_list(table_name, key, customer_data, primary_key)
                else:
                    parse_object(table_name, key, customer_data, foreign_key_name, foreign_key, index)

        def parse_object(table_name, key, customer_data, foreign_key_name, foreign_key, index):
            if index == 0:
                table_data[table_name].append({})
            table_size = len(table_data[table_name])
            if foreign_key_name and foreign_key:
                table_data[table_name][table_size - 1][foreign_key_name] = foreign_key
            table_data[table_name][table_size - 1][key] = customer_data[key]

        def flatten_simple_dict(data, table_name, index):
            for d_key in data:
                new_key = f"{table_name}_{d_key}"
                if len(table_data[table_name]) < index + 1:
                    table_data[table_name].append({})
                table_data[table_name][index][new_key] = data[d_key]

        parse_nested_dict(data_object, main_table_name)
        return table_data

    @staticmethod
    def _is_list_of_dicts(object_):
        type_of_var = type(object_)
        if type_of_var != list:
            return False
        return all(isinstance(i, dict) for i in object_)

    @staticmethod
    def validate_parser_input(json_data):
        if not isinstance(json_data, list):
            raise ParserException("Data input to parser must be a list of dictionaries")
