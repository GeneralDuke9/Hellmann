import datetime

import netCDF4  # type: ignore
import requests

from client import KNMIClient


API_EXPIRATION_DATE = datetime.date(2022, 6, 1)
API_KEY = (
    "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJp"
    "ZCI6ImNjOWE2YjM3ZjVhODQwMDZiMWIzZGIzZDRjYzVjODFiIiwiaCI6Im11cm11cjEyOCJ9"
)
API_URL = "https://api.dataplatform.knmi.nl/open-data/v1/datasets/"


def get_netcdf(client: KNMIClient):
    print("List")
    etmaalgegevens_list = client.list_etmaalgegevens()
    assert etmaalgegevens_list.result_count == 1
    filename = etmaalgegevens_list.files[0].filename
    print("Get link")
    etmaalgegevens_link = client.get_etmaalgegevens(filename)
    etmaalgegevens_download_link = etmaalgegevens_link.temporary_download_url
    print("Get file")
    etmaalgegevens = requests.get(etmaalgegevens_download_link)
    with open("testfile.nc", "wb") as file:
        file.write(etmaalgegevens.content)
    return netCDF4.Dataset("from-memory", mode="r", memory=etmaalgegevens.content)


def main():
    client = KNMIClient(API_URL, API_KEY, API_EXPIRATION_DATE)
    netcdf = get_netcdf(client)
    import pdb

    pdb.set_trace()


if __name__ == "__main__":
    main()
