#!/bin/python3
import csv
import os
import sys
from typing import Any, Dict, OrderedDict, Tuple, Union

import xmltodict


class InvalidCFDI(Exception):
    pass


def get_cfdi_dict(file_path: str) -> OrderedDict:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    xml_dict = xmltodict.parse(
        content,
        namespaces={
            "cfdi": None,
            "nomina": None,
            "nomina11": None,
            "Nomina11": None,
            "nomina12": None,
            "Nomina12": None,
            "pago10": None,
            "Pago10": None,
            "pago20": None,
            "Pago20": None,
        },
    )
    comprobante = xml_dict.get("Comprobante")
    if not comprobante:
        print(f"{file_path} is not a CFDI")
    return comprobante

def get_tfd(cfdi_dict: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(cfdi_dict["Complemento"], list):
        for complemento in cfdi_dict["Complemento"]:
            if complemento.get("tfd:TimbreFiscalDigital"):
                return complemento["tfd:TimbreFiscalDigital"]
    elif cfdi_dict.get("Complemento") and cfdi_dict["Complemento"].get("tfd:TimbreFiscalDigital"):
        return cfdi_dict["Complemento"]["tfd:TimbreFiscalDigital"]
    raise InvalidCFDI("No TimbreFiscalDigital found")

def process(file_path: str) -> Tuple[str, str]:
    cfdi_dict = get_cfdi_dict(file_path)
    tfd = get_tfd(cfdi_dict)
    uuid = tfd["@UUID"]
    return (uuid, file_path)

def main(xmls_path: str):
    # Process all .xml files in the given path
    res = [
        process(os.path.join(xmls_path, file_path))
        for file_path in os.listdir(xmls_path) if file_path.endswith(".xml")
    ]
    # Write the results to a csv file
    with open("uuids.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(res)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python3 uuids.py <carpeta_con_xmls> <archivo_de_resultados>")
        print("Recuda instalar las dependencias con: pip3 install -r requirements.txt")
        sys.exit(1)
    xmls_path = sys.argv[1]
    res_path = sys.argv[2]
    main(xmls_path)
