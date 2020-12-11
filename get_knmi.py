import requests

knmi_url: str = "http://projects.knmi.nl/klimatologie/daggegevens/getdata_dag.cgi"

payload = {
    "lang": "nl",
    "byear": "2020",
    "bmonth": "12",
    "bday": "11",
    "eyear": "2020",
    "emonth": "12",
    "eday": "11",
    "variabele": "TG",
    "stations": [
        "210",
        "235",
        "240",
        "242",
        "249",
        "251",
        "257",
        "260",
        "267",
        "269",
        "270",
        "273",
        "275",
        "277",
        "278",
        "279",
        "280",
        "283",
        "286",
        "290",
        "310",
        "319",
        "323",
        "330",
        "340",
        "344",
        "348",
        "350",
        "356",
        "370",
        "375",
        "377",
        "380",
        "391",
    ],
    "submit": "Download+data+set",
}

response = requests.get(knmi_url, params=payload)
update = response.text
print(update)
