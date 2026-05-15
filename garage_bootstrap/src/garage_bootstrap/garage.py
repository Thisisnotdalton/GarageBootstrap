import os.path
from functools import lru_cache

import garage_admin_sdk
from garage_bootstrap.settings import get_settings
from garage_bootstrap.models import Key, KeyName, KeyID, KeySecret, BucketName, BucketID, Bucket, GarageConfiguration


def get_configuration() -> garage_admin_sdk.Configuration:
    settings = get_settings()
    return garage_admin_sdk.Configuration(
        host=settings.api_url,
        access_token=settings.api_key
    )


@lru_cache
def get_api_client() -> garage_admin_sdk.ApiClient:
    return garage_admin_sdk.ApiClient(get_configuration())


@lru_cache
def get_keys_api() -> garage_admin_sdk.AccessKeyApi:
    return garage_admin_sdk.AccessKeyApi(get_api_client())


@lru_cache
def get_permissions_api() -> garage_admin_sdk.PermissionApi:
    return garage_admin_sdk.PermissionApi(get_api_client())


@lru_cache
def get_buckets_api() -> garage_admin_sdk.BucketApi:
    return garage_admin_sdk.BucketApi(get_api_client())


def get_existing_keys(remove_expired: bool = True) -> dict[KeyName, KeyID]:
    existing_keys = {}
    expired_key_ids = []
    for key in get_keys_api().list_keys():
        if remove_expired and key.expired:
            expired_key_ids.append(key.id)
            continue
        existing_keys[key.name] = key.id
    for key_id in expired_key_ids:
        get_keys_api().delete_key(key_id)
    return existing_keys


def delete_keys(key_names: list[KeyName]):
    keys = get_existing_keys(remove_expired=False)
    for key_name in key_names:
        if keys.get(key_name):
            get_keys_api().delete_key(keys[key_name])


def get_existing_buckets() -> dict[BucketName, BucketID]:
    existing_buckets = {}
    for bucket in get_buckets_api().list_buckets():
        assert len(
            bucket.global_aliases) == 1, f'Bucket must have exactly one global alias: {bucket.id}: {bucket.global_aliases}'
        existing_buckets[bucket.global_aliases[0]] = bucket.id
    return existing_buckets


def create_buckets(buckets: list[Bucket]) -> list[BucketName]:
    bucket_names = []
    buckets_api = get_buckets_api()
    existing_buckets = get_existing_buckets()
    for bucket in buckets:
        if bucket.name not in existing_buckets:
            new_bucket_params = {
                'globalAlias': [bucket.name]
            }
            new_bucket = buckets_api.create_bucket(garage_admin_sdk.CreateBucketRequest.from_dict(new_bucket_params))
            bucket_names.append(bucket.name)
            existing_buckets[bucket.name] = new_bucket.id
        quotas = {
            'maxBytes': bucket.max_size,
            'maxObjects': bucket.max_objects,
        }
        buckets_api.update_bucket(
            existing_buckets[bucket.name],
            garage_admin_sdk.UpdateBucketRequestBody.from_dict(dict(quotas=quotas))
        )
    return bucket_names


def create_keys(keys: list[Key], regenerate: bool = False) -> dict[KeyName, KeySecret]:
    key_secrets = {}
    keys_api = get_keys_api()
    permissions_api = get_permissions_api()
    if regenerate:
        delete_keys([key.name for key in keys])
    existing_keys = get_existing_keys()
    existing_buckets = get_existing_buckets()
    for key in keys:
        key_id = existing_keys.get(key.name)
        if key_id is None:
            bucket_create_permission = 'allow' if key.create_bucket_permission else 'deny'
            new_key_params = {
                'name': key.name,
                bucket_create_permission: {
                    'createBucket': True
                }
            }
            new_key_request_body = garage_admin_sdk.UpdateKeyRequestBody.from_dict(new_key_params)
            new_key = keys_api.create_key(new_key_request_body)
            key_secrets[key.name] = KeySecret(id=new_key.access_key_id, secret=new_key.secret_access_key)
            key_id = new_key.access_key_id
        listed_bucket_names = {}
        for permission in key.permissions:
            listed_bucket_names[permission.bucket_name] = True
            allowed_permissions = dict()
            denied_permissions = dict()
            (allowed_permissions if permission.read else denied_permissions)['read'] = True
            (allowed_permissions if permission.write else denied_permissions)['write'] = True
            if any(allowed_permissions):
                allowed_permissions_params = {
                    'accessKeyId': key_id,
                    'bucketId': existing_buckets[permission.bucket_name],
                    'permissions': allowed_permissions,
                }
                permissions_api.allow_bucket_key(
                    garage_admin_sdk.BucketKeyPermChangeRequest.from_dict(allowed_permissions_params))
            if any(denied_permissions):
                denied_permissions_params = {
                    'accessKeyId': key_id,
                    'bucketId': existing_buckets[permission.bucket_name],
                    'permissions': denied_permissions,
                }
                permissions_api.deny_bucket_key(
                    garage_admin_sdk.BucketKeyPermChangeRequest.from_dict(denied_permissions_params))
        for bucket_name in existing_buckets:
            if not listed_bucket_names.get(bucket_name):
                denied_permissions_params = {
                    'accessKeyId': key_id,
                    'bucketId': existing_buckets[bucket_name],
                    'permissions': {'read': True, 'write': True},
                }
                permissions_api.deny_bucket_key(
                    garage_admin_sdk.BucketKeyPermChangeRequest.from_dict(denied_permissions_params))
    return key_secrets


def apply_configuration(configuration: GarageConfiguration, output_directory: str = '.'):
    create_buckets(configuration.buckets)
    generated_key_secrets = create_keys(configuration.keys)
    os.makedirs(output_directory, exist_ok=True)
    for key_name, key_secret in generated_key_secrets.items():
        with open(os.path.join(output_directory, f'{key_name}.json'), 'w') as f:
            f.write(key_secret.model_dump_json(indent=2, exclude_none=True))
