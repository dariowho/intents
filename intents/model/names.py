"""
Intent and Entity names must respect some constraints. :func:`check_name` documents
and implements those constraints.
"""
import re

def check_name(candidate_name: str, is_system: bool=False):
    """
    Raise `ValueError` if the given Intent or Entity name is not a valid name.
    Valid names

    * Only contain letter, underscore (`_`) and period (`.`) characters
    * Start with a letter
    * Don't contain repeated underscores (e.g. `__`)
    * Don't start wit `i_`. This is a reserved prefix for *Intents* system
      intents
    
    Note that `Agent.register` will apply further checks to spot duplicate
    names. Note that names are case insensitive, and shouldn't overlap
    with parameter names.

    Args:
        candidate_name: The Intent or Entity name to check
        is_system: When True, allow reserved names (those starting with `i_`)
    """
    invalid_reason = None
    
    if re.search(r'[^a-zA-Z_\.]', candidate_name):
        invalid_reason = "must only contain letters, underscore or period"

    if candidate_name.startswith('.') or candidate_name.startswith('_'):
        invalid_reason = "must start with a letter"

    if "__" in candidate_name:
        invalid_reason = "must not contain __"

    if candidate_name.lower().startswith("i_") and not is_system:
        invalid_reason = "the 'i_' prefix is reserved for system intents and entities"

    if invalid_reason:
        raise ValueError(f"Invalid name '{candidate_name}': {invalid_reason}. "
            "If the issue is related to your class name or path you can either change names to "
            "be compliant, or use a custom name by setting 'Intent.name' manually. See the "
            "documentation at https://intents.readthedocs.io/ for more information on intent "
            "naming rules.")
