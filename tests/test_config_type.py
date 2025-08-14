from pathlib import Path
from datetime import time, date
from mgconfig import ConfigTypes

test_values = {
    'str': 'teststring',
    'int': 500,
    'float': 3.1,
    'bool': False,
    # 'seconds': 40,
    # 'minutes': 20,
    'secret': 'hidden',
    'date': date(2024, 10, 23),
    'time': time(9, 11, 25),
    'path': Path(r'\dir\b.txt'),
    # 'filename': 'myfile.txt',
    'bytes': b'xyz',
    'hidden': 'test'
}

invalid_values = {
    'str': False,
    'int': 500.3,
    'float': 'test',
    'bool': 'test',
    # 'seconds': 40.1,
    # 'minutes': 20.1,
    'secret': 30,
    'date': time(9, 11, 25),
    'time': date(2024, 10, 23),
    'path': date(2024, 10, 23),
    # 'filename': 30,
    'bytes': False,
    # 'hidden': 'test'
}

invalid_values_2 = {
    'seconds': -5,
    'minutes': -5,
    'filename': 'my*file.txt',
}



def test_config_types():
    def prep(value):
        return (f'{value}: {type(value).__name__}').ljust(25)

    # check if all types have test values
    for val_type in ConfigTypes._config_types:
        assert val_type in test_values

    print(f'{prep("val_type")} {prep("value")} {prep("parsed_value")} {prep("output")} {prep("display")}')
    print('-'*130)
    for val_type, value in test_values.items():
        # check display function
        display = ConfigTypes.display_value(value, val_type)
        assert type(display) == str

        # check output function
        output = ConfigTypes.output_value(value, val_type)

        # check parse function
        result, parsed_value = ConfigTypes.parse_value(
            output, val_type)

        assert result
        assert value == parsed_value

        print(
            f'{prep(val_type)} {prep(value)} {prep(parsed_value)} {prep(output)} {prep(display)}')

    for val_type, value in invalid_values.items():
        # check output function
        try:
            output = ConfigTypes.output_value(value, val_type)     
            assert False   
        except ValueError as e:
            print(e)
            assert str(e).startswith('Type of value is not compatible with configuration type')

    for val_type, value in invalid_values.items():
        # check output function
        try:
            output = ConfigTypes.output_value(value, val_type)     
            assert False   
        except ValueError as e:
            print(e)
            assert str(e).startswith('Type of value is not compatible with configuration type')          

    # for val_type, value in invalid_values_2.items():
    #     # check output function and parse function
    #     try:
    #         output = ConfigTypes.output_value(value, val_type)     
    #         result, parsed_value = ConfigTypes.parse_value(output, val_type)
    #         assert not result    
    #     except Exception as e:
    #         assert False             

if __name__ == '__main__':
    test_config_types()
