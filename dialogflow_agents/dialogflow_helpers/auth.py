from typing import Union

import google.oauth2.service_account
from google.auth.credentials import Credentials


def resolve_credentials(credentials_or_path: Union[str, Credentials]) -> Credentials:
    """
    Determine whether the given object is a valid instance of
    :class:`Credentials`, or a path to a Service Account JSON. In the latter
    case, the JSON is read into an instance of
    :class:`google.oauth2.service_account.Credetials`
    (https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.service_account.html)
    """
    if isinstance(credentials_or_path, Credentials):
        return credentials_or_path

    elif isinstance(credentials_or_path, str):
        return google.oauth2.service_account.Credentials.from_service_account_file(credentials_or_path)
        
    else:
        raise ValueError("Unsupported Dialogflow Credentials type. Please pass the path to a Service Account JSON, or an instance of google.auth.credentials.Credentials")
