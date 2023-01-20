import logging
import mimetypes
import tempfile
from abc import ABC, abstractmethod
from urllib.parse import urlencode

from django.utils.archive import Archive

from .utils import download_file


class ArgumentParseableDataSource(ABC):
    @property
    @abstractmethod
    def CLI_NAME(self):
        return NotImplementedError

    @classmethod
    def add_arguments(cls, parser):
        cls.add_custom_arguments(parser=parser)

    @classmethod
    @abstractmethod
    def add_custom_arguments(cls, parser):
        return NotImplementedError


class BaseDataSource(ArgumentParseableDataSource, ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__()


class CompressedDataSourceMixin:
    @property
    def COMPRESSED_DESIRED_FILENAME(self):
        return None

    @classmethod
    def get_compressed_desired_filename(cls, desired_filename=None, **kwargs):
        desired_filename = desired_filename or cls.COMPRESSED_DESIRED_FILENAME
        return desired_filename.format(**kwargs) if desired_filename else None


class FileDataSource(BaseDataSource, CompressedDataSourceMixin):
    @classmethod
    def _process_file(cls, file_path, **kwargs):
        if compressed_file := cls.get_compressed_desired_filename(**kwargs):
            return Archive(file_path)._archive._archive.open(compressed_file)
        else:
            return open(file_path)

    def __init__(self, file_path, **kwargs) -> None:
        self.file_path = file_path
        self.file = (
            self._process_file(file_path=file_path, **kwargs) if file_path else None
        )


class OnlineDataSource(BaseDataSource, ABC):
    @property
    @abstractmethod
    def URL(self):
        return NotImplementedError

    @classmethod
    def _construct_url(cls, url=None, params=[], **kwargs):
        url = url or cls.URL
        url = url.format(**kwargs)
        logging.debug(f"Url {url}")
        return "?".join((url, urlencode(params))) if params else url

    @classmethod
    def from_online_source(cls, **kwargs):
        return cls(url=cls._construct_url(**kwargs), **kwargs)

    def __init__(self, url=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.url = url


class DownloadableDataSource(FileDataSource, OnlineDataSource):

    DOWNLOAD_FILE_SUFFIX = None  # Force if we don't want to guess using its mimetype.
    URL = None
    CLI_NAME = "simple_downloadable_datasource"

    @classmethod
    def add_custom_arguments(cls, parser):
        pass

    @classmethod
    def get_download_file_extension(cls, url):
        return cls.DOWNLOAD_FILE_SUFFIX or mimetypes.guess_extension(
            type=mimetypes.guess_type(url=url)[0]
        )

    @classmethod
    def from_online_source(cls, **kwargs):
        url = kwargs.pop("url", None)
        url = cls._construct_url(url=url, **kwargs)
        with tempfile.NamedTemporaryFile(
            delete=True, suffix=cls.get_download_file_extension(url=url)
        ) as tmpfile:
            instance = cls(
                url=url,
                file_path=download_file(url=url, filename=tmpfile.name),
                **kwargs,
            )
        return instance
