from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Type

import requests
from requests import Response


class ApiError(Exception):
    pass


class BadRequestError(ApiError):
    pass


class UnauthorizedError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class MethodNotAllowedError(ApiError):
    pass


class InternalServerError(ApiError):
    pass


class BadGatewayError(ApiError):
    pass


class ServiceUnavailableError(ApiError):
    pass


class GatewayTimeoutError(ApiError):
    pass


response_error_by_status_code: dict[int, Type[ApiError]] = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    405: MethodNotAllowedError,
    500: InternalServerError,
    502: BadGatewayError,
    503: ServiceUnavailableError,
    504: GatewayTimeoutError,
}


class KeyExpiredError(Exception):
    pass


@dataclass
class FileDetails:
    filename: str
    size: str
    last_modified: str

    @classmethod
    def from_response(cls, response: dict) -> FileDetails:
        return FileDetails(filename=response["filename"], size=response["size"], last_modified=response["lastModified"])


@dataclass
class FileDownload:
    content_type: str | None
    last_modified: str | None
    size: int | None
    temporary_download_url: str

    @classmethod
    def from_response(cls, response: Response) -> FileDownload:
        response_json = response.json()
        return FileDownload(
            content_type=response_json["contentType"],
            last_modified=response_json["lastModified"],
            size=response_json["size"],
            temporary_download_url=response_json["temporaryDownloadUrl"],
        )


@dataclass
class DatasetFiles:
    is_truncated: bool
    files: list[FileDetails]
    result_count: int
    max_results: int | None
    start_after_filename: str | None

    @classmethod
    def from_response(cls, response: Response) -> DatasetFiles:
        response_json = response.json()
        return DatasetFiles(
            is_truncated=response_json["isTruncated"],
            files=[FileDetails.from_response(file) for file in response_json["files"]],
            result_count=response_json["resultCount"],
            max_results=response_json["maxResults"],
            start_after_filename=response_json["startAfterFilename"],
        )


class KNMIClient:
    def __init__(self, url: str, key: str, expiration_date: datetime.date):
        self.expiration_date = expiration_date
        self.key = key
        self.url = url

        if expiration_date <= datetime.date.today():
            raise KeyExpiredError

        self.session = requests.session()
        self._add_authentication()

    def _add_authentication(self):
        auth_headers = {"Authorization": self.key}
        self.session.headers.update(auth_headers)

    def _get_endpoint(self, dataset_name: str, version_id: str, filename: str) -> FileDownload:
        response = self.session.get(self.url + f"{dataset_name}/versions/{version_id}/files/{filename}/url")

        if response.status_code > 300:
            raise response_error_by_status_code[response.status_code](response.text)

        return FileDownload.from_response(response)

    def _list_endpoint(self, dataset_name: str, version_id: str, params: dict = None) -> DatasetFiles:
        response = self.session.get(self.url + f"{dataset_name}/versions/{version_id}/files", params=params)

        if response.status_code > 300:
            raise response_error_by_status_code[response.status_code](response.text)

        return DatasetFiles.from_response(response)

    def list_vochtigheid_en_temperatuur(self, max_keys: int = None) -> DatasetFiles:
        if max_keys:
            params = {"maxKeys": max_keys}
        else:
            params = {}
        return self._list_endpoint(dataset_name="vochtigheid_en_temperatuur", version_id="1.0", params=params)

    def get_vochtigheid_en_temperatuur(self, filename: str) -> FileDownload:
        return self._get_endpoint(dataset_name="vochtigheid_en_temperatuur", version_id="1.0", filename=filename)

    def list_etmaalgegevens(self, max_keys: int = None) -> DatasetFiles:
        if max_keys:
            params = {"maxKeys": max_keys}
        else:
            params = {}
        return self._list_endpoint(dataset_name="etmaalgegevensKNMIstations", version_id="1", params=params)

    def get_etmaalgegevens(self, filename: str) -> FileDownload:
        return self._get_endpoint(dataset_name="etmaalgegevensKNMIstations", version_id="1", filename=filename)

    def list_actuele_10min_data(self, max_keys: int = None) -> DatasetFiles:
        if max_keys:
            params = {"maxKeys": max_keys}
        else:
            params = {}
        return self._list_endpoint(dataset_name="Actuele10mindataKNMIstations", version_id="2", params=params)

    def get_actuele_10min_data(self, filename: str) -> FileDownload:
        return self._get_endpoint(dataset_name="Actuele10mindataKNMIstations", version_id="2", filename=filename)
