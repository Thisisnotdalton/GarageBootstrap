from typing import Annotated, Optional
from pydantic import BaseModel, Field

BucketID = Annotated[str, Field(description='Unique identifier of the bucket.')]
BucketName = Annotated[str, Field(description='Name of the bucket.')]
KeyID = Annotated[str, Field(description='Unique identifier of the key.')]
KeyName = Annotated[str, Field(description='Name of the key.')]


class KeyPermission(BaseModel):
    bucket_name: BucketName
    read: bool
    write: bool


class Key(BaseModel):
    name: KeyName
    permissions: list[KeyPermission]
    create_bucket_permission: Annotated[
        bool, Field(description='Whether the key has permission to create buckets.')] = False


class KeySecret(BaseModel):
    id: KeyID
    secret: str


class Bucket(BaseModel):
    name: BucketName
    max_size: Optional[Annotated[int, Field(description='Maximum size of the bucket in bytes.')]] = None
    max_objects: Optional[Annotated[int, Field(description='Maximum number of objects this bucket may hold.')]] = None


class GarageConfiguration(BaseModel):
    buckets: list[Bucket]
    keys: list[Key]
