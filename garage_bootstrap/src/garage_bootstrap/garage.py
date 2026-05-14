from functools import lru_cache

import garage_admin_sdk
from garage_bootstrap.settings import get_settings
from garage_bootstrap.models import Key, KeyName, KeyID, Bucket, GarageConfiguration


def get_configuration() -> garage_admin_sdk.Configuration:
    settings = get_settings()
    return garage_admin_sdk.Configuration(
        host=settings.garage_api_url,
        access_token=settings.garage_api_key
    )


@lru_cache
def get_api_client() -> garage_admin_sdk.ApiClient:
    return garage_admin_sdk.ApiClient(get_configuration())


@lru_cache
def get_keys_api() -> garage_admin_sdk.AccessKeyApi:
    return garage_admin_sdk.AccessKeyApi(get_api_client())


def get_existing_keys() -> dict[KeyName, KeyID]:
    existing_keys = {}
    for key in get_keys_api().list_keys():
        existing_keys[key.name] = key.id
    return existing_keys


def create_keys(keys: list[Key]) -> list[KeyName]:
    key_names = []
    keys_api = get_keys_api()
    existing_keys = get_existing_keys()
    for key in keys:
        if not existing_keys.get(key.name):
            bucket_create_permission = 'allow' if key.create_bucket_permission else 'deny'
            new_key_params = {
                'name': key.name,
                bucket_create_permission: {
                    'createBucket': True
                }
            }
            new_key_request_body = garage_admin_sdk.UpdateKeyRequestBody.from_dict(new_key_params)
            new_key = keys_api.create_key(new_key_request_body)
            key_names.append(new_key.name)
    return key_names
