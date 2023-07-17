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
        cls._add_custom_arguments(parser=parser)

    @classmethod
    @abstractmethod
    def _add_custom_arguments(cls, parser):
        return NotImplementedError


class BaseDataSource(ArgumentParseableDataSource, ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__()


class CompressedDataSourceMixin:
    COMPRESSED_DESIRED_FILENAME = None

    @classmethod
    def _get_compressed_desired_filename(cls, desired_filename=None, **kwargs):
        desired_filename = desired_filename or cls.COMPRESSED_DESIRED_FILENAME
        return desired_filename.format(**kwargs) if desired_filename else None


class FileDataSource(CompressedDataSourceMixin, BaseDataSource):
    @classmethod
    def _process_file(cls, file_path, **kwargs):
        if compressed_file := cls._get_compressed_desired_filename(**kwargs):
            return Archive(file_path)._archive._archive.open(compressed_file)
        else:
            return open(file_path)

    def __init__(self, file_path, **kwargs) -> None:
        self.file_path = file_path
        self.file = (
            self._process_file(file_path=file_path, **kwargs) if file_path else None
        )
        super().__init__(**kwargs)


class OnlineDataSource(BaseDataSource, ABC):
    @property
    @abstractmethod
    def URL(self):
        return NotImplementedError

    @classmethod
    def _construct_url(cls, url=None, params={}, **kwargs):
        url = url or cls.URL
        url = url.format(**kwargs)
        logging.debug(f"Url {url}")
        return "?".join((url, urlencode(params))) if params else url

    @classmethod
    def from_online_source(cls, **kwargs):
        url = kwargs.pop("url", None)
        return cls(url=cls._construct_url(url=url, **kwargs), **kwargs)

    def __init__(self, url=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.url = url


class DownloadableDataSource(FileDataSource, OnlineDataSource):
    DOWNLOAD_FILE_SUFFIX = None  # Force if we don't want to guess using its mimetype.
    URL = None
    CLI_NAME = "simple_downloadable_datasource"

    @classmethod
    def _add_custom_arguments(cls, parser):
        pass

    @classmethod
    def _get_download_file_extension(cls, url):
        return cls.DOWNLOAD_FILE_SUFFIX or mimetypes.guess_extension(
            type=mimetypes.guess_type(url=url)[0]
        )

    @classmethod
    def from_online_source(cls, **kwargs):
        url = kwargs.pop("url", None)
        url = cls._construct_url(url=url, **kwargs)
        with tempfile.NamedTemporaryFile(
            delete=True, suffix=cls._get_download_file_extension(url=url)
        ) as tmpfile:
            instance = cls(
                url=url,
                file_path=download_file(url=url, filename=tmpfile.name),
                **kwargs,
            )
        return instance
