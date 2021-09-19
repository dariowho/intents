import re

def camel_to_snake_case(name: str) -> str:
    """
    Source: https://stackoverflow.com/a/1176023

    Args:
        name: A CamelCase name

    Returns:
        A snake_case version of the input name
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower()
