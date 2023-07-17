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

    def _validate_uri(cls, uri):
        if not cls.matches_uri(uri=uri):
            raise ValueError(f"Scheme for {uri} is not supported in {cls}")

    def get_vsi_path(self, uri):
        self._validate_uri(uri=uri)
        return self.format_syntax(name=self.NAME, uri=uri, **self.options)


class OnlineGdalFileHandler(GdalVirtualFileHandler):
    # See: https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access

    NAME = "vsicurl"
    SYNTAX = "/{name}{url_encoded_params}{url}"
    ALLOWED_SCHEMES = ("http", "https", "ftp")

    @classmethod
    def format_syntax(cls, name, uri, **kwargs):
        url_encoded_params = ""
        if kwargs:
            # Add url param with the path if other params
            url_encoded_params = "?" + urlencode(kwargs)
            url_encoded_params += f"&url={uri}"

        return super().format_syntax(
            name=name,
            url="/" + uri if not url_encoded_params else "",
            url_encoded_params=url_encoded_params,
        )


class BucketGdalFileHandler(GdalVirtualFileHandler):
    # See: https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access

    ALLOWED_SCHEMES = ("s3", "gs")

    S3_NAME = "vsis3"
    GS_NAME = "vsigs"

    # Dict -> keys: scheme, value NAME
    NAME = {"s3": S3_NAME, "gs": GS_NAME}

    SYNTAX = "/{name}/{uri}"

    def get_vsi_path(self, uri):
        self._validate_uri(uri=uri)
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
        mime_type, encoding = mimetypes.guess_type(url=uri)
        logging.debug(f"mimetype is {mime_type}")

        if mime_type is None:
            return encoding

        extension = mimetypes.guess_extension(type=mime_type)
        try:
            return cls.INFER_COMPRESSION_DICT[extension]
        except KeyError:
            if encoding:
                return encoding
            else:
                return None

    @classmethod
    def matches_uri(cls, uri):
        """Returns True if this FS can be used for the given URI/mode pair.
        Args:
            uri: URI of file
        """
        return cls.guess_compression_type(uri) in cls.ALLOWED_COMPRESSIONS

    def get_vsi_path(self, path, dst_path=""):
        self._validate_uri(uri=path)

        compression_type = self.guess_compression_type(uri=path)

        # Cas None to ""
        dst_path = dst_path or ""
        uri = path
        if dst_path:
            uri = os.path.join(path, dst_path.lstrip("/"))

        return self.format_syntax(
            name=self.NAME[compression_type],
            uri=uri,
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
    if urlparse(url=uri).scheme:
        if OnlineGdalFileHandler.matches_uri(uri=uri):
            result = OnlineGdalFileHandler(options=options).get_vsi_path(uri=uri)
        elif BucketGdalFileHandler.matches_uri(uri=uri):
            result = BucketGdalFileHandler(options=options).get_vsi_path(uri=uri)
        else:
            raise ValueError("Uri does not matches any file handler.")

    if CompressedGdalFile.matches_uri(uri=result):
        result = CompressedGdalFile(options=options).get_vsi_path(
            path=result,
            dst_path=dst_file,
        )

    return result
