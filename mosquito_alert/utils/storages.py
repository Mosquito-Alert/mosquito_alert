from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


class StaticRootS3Boto3Storage(S3StaticStorage):
    location = "static"
    default_acl = "public-read"


class MediaRootS3Boto3Storage(S3Boto3Storage):
    location = "media"
    file_overwrite = False
    default_acl = "public-read"
