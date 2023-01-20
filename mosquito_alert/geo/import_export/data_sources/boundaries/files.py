import logging
import mimetypes
import os
from abc import ABC, abstractmethod
from urllib.parse import urlencode, urlparse


class GdalVirtualFileHandler(ABC):

    SYNTAX = "/{name}/{uri}"

    @classmethod
    def matches_uri(cls, uri):
        """Returns True if this FS can be used for the given URI/mode pair.
        Args:
            uri: URI of file
        """
        return urlparse(uri).scheme in cls.ALLOWED_SCHEMES

    @property
    @abstractmethod
    def ALLOWED_SCHEMES(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def NAME(self):
        raise NotImplementedError

    def __init__(self, options={}):
        self.options = options

    @classmethod
    def format_syntax(cls, name, **kwargs):
        return cls.SYNTAX.format(name=name, **kwargs)

    def get_vsi_path(self, uri=None):
        return self.format_syntax(name=self.NAME, uri=uri, **self.options)


class OnlineGdalFileHandler(GdalVirtualFileHandler):
    # See: https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access

    NAME = "vsicurl"
    SYNTAX = "/{name}{url_encoded_params}/{url}"
    ALLOWED_SCHEMES = ("http", "https", "ftp")

    @classmethod
    def format_syntax(cls, name, uri, **kwargs):
        if kwargs:
            # Add url param with the path if other params
            kwargs["url"] = uri

        return super().format_syntax(
            name=name,
            url_encoded_params="?" + urlencode(kwargs) if kwargs else "",
            url=kwargs.get("url") or uri,
        )


class BucketGdalFileHandler(GdalVirtualFileHandler):
    # See: https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access

    ALLOWED_SCHEMES = ("s3", "gs")

    S3_NAME = "vsis3"
    GS_NAME = "vsigs"

    # Dict -> keys: scheme, value NAME
    NAME = {"s3": S3_NAME, "gs": GS_NAME}

    SYNTAX = "/{name}/{uri}"

    def get_vsi_path(self, uri=None):
        parsed = urlparse(uri)
        bucket_type = parsed.scheme
        logging.debug(f"Detected {bucket_type} bucket")
        return self.format_syntax(
            name=self.NAME[bucket_type], uri=parsed.netloc + parsed.path, **self.options
        )


class CompressedGdalFile(GdalVirtualFileHandler):
    # See: https://gdal.org/user/virtual_file_systems.html#vsizip-zip-archives

    ALLOWED_SCHEMES = -1  # ALL

    COMPRESSION_ZIP = "zip"
    COMPRESSION_GZIP = "gzip"
    COMPRESSION_TAR = "tar"
    ALLOWED_COMPRESSIONS = [COMPRESSION_ZIP, COMPRESSION_GZIP, COMPRESSION_TAR]

    # NOTE: get the dict keys from mimetypes.types_map.keys()
    INFER_COMPRESSION_DICT = {
        ".zip": "zip",
        ".gz": "gzip",
        ".tar": "tar",
    }

    NAME = {
        COMPRESSION_ZIP: "vsizip",
        COMPRESSION_GZIP: "vsigzip",
        COMPRESSION_TAR: "vsitar",
    }

    @classmethod
    def guess_compression_type(cls, uri):
        logging.debug(f"Guessing compression type for {uri}")
        mime_type, _ = mimetypes.guess_type(url=uri)
        logging.debug(f"mimetype is {mime_type}")

        if not mime_type:
            return None

        extension = mimetypes.guess_extension(type=mime_type)
        try:
            result = cls.INFER_COMPRESSION_DICT[extension]
            logging.debug(f"Compression type is {result}")
        except KeyError:
            return None
        return result

    @classmethod
    def matches_uri(cls, uri):
        """Returns True if this FS can be used for the given URI/mode pair.
        Args:
            uri: URI of file
        """
        return cls.guess_compression_type(uri) in cls.ALLOWED_COMPRESSIONS

    def get_vsi_path(self, path=None, dst_path=None, compression_type=None):
        if compression_type and compression_type not in self.ALLOWED_COMPRESSIONS:
            raise ValueError(
                f"compression_type must be one of {self.ALLOWED_COMPRESSIONS}"
            )

        if not compression_type:
            compression_type = self.guess_compression_type(uri=path)

        return self.format_syntax(
            name=self.NAME[compression_type],
            uri=os.path.join(path, dst_path) if dst_path else path,
            **self.options,
        )


def uri_to_vsi_path(uri: str, options={}) -> str:
    """A function to convert URIs to VSI path strings
    Args:
        uri: URI of the file, possibly nested within archives as follows
            <archive_URI>!path/to/contained/file.ext
            Acceptable URI schemes are file, s3, gs, http, https, and ftp
            Allowable compression types are tar, zip, and gzip
    """

    archive_content = uri.rfind("!")
    dst_file = None
    if archive_content != -1:
        dst_file = uri[archive_content + 1 :]  # noqa: E203
        uri = uri[:archive_content]

    result = uri
    # regular URI
    if OnlineGdalFileHandler.matches_uri(uri=uri):
        result = OnlineGdalFileHandler(options=options).get_vsi_path(uri=uri)
    elif BucketGdalFileHandler.matches_uri(uri=uri):
        result = BucketGdalFileHandler(options=options).get_vsi_path(uri=uri)

    if CompressedGdalFile.matches_uri(uri=result):
        result = CompressedGdalFile(options=options).get_vsi_path(
            path=result,
            dst_path=dst_file,
        )

    return result
