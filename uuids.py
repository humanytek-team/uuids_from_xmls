#!/bin/python3
import csv
import logging
import os
import shutil
import sys
from typing import Any, Dict, OrderedDict, Tuple, Union

import xmltodict

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.ERROR)

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
        raise InvalidCFDI(f"No Comprobante found in XML {file_path}")
    return comprobante

def get_tfd(cfdi_dict: Dict[str, Any]) -> Dict[str, Any]:
    v_complemento = cfdi_dict.get("Complemento")
    if not v_complemento:
        raise InvalidCFDI("Complemento not found in CFDI")
    if isinstance(v_complemento, list):
        for complemento in v_complemento:
            if complemento.get("tfd:TimbreFiscalDigital"):
                return complemento["tfd:TimbreFiscalDigital"]
    elif cfdi_dict.get("Complemento") and v_complemento.get("tfd:TimbreFiscalDigital"):
        return v_complemento["tfd:TimbreFiscalDigital"]
    raise InvalidCFDI("No TimbreFiscalDigital found")

def process(file_path: str) -> Tuple[str, str]:
    cfdi_dict = get_cfdi_dict(file_path)
    try:
        tfd = get_tfd(cfdi_dict)
    except InvalidCFDI as e:
        raise InvalidCFDI(f"{file_path}: {e}")
    uuid = tfd["@UUID"]
    return (uuid, file_path)

def main(xmls_path: str, uuids_path, output_path: str) -> None:
    # Process all .xml files in the given path
    with open(uuids_path, "r") as f:
        reader = csv.reader(f)
        uuids: set[str] = {row[0] for row in reader}
    # Get all files, including subdirectories
    for root, _, files in os.walk(xmls_path):
        for file in files:
            if not file.endswith(".xml"):
                continue
            file_path = os.path.join(root, file)
            try:
                uuid, file_path = process(file_path)
            except InvalidCFDI:
                _logger.warning(f"{file_path} is not a valid CFDI")
                continue
            if uuid in uuids:
                _logger.info(f"Copying {file_path} to {output_path}")
                file_output_path = os.path.join(output_path, f"{uuid}.xml")
                shutil.copy(file_path, file_output_path)
                uuids.remove(uuid)
    _logger.warning(f"UUIDs not found: {uuids}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Uso: python3 uuids.py <carpeta_con_xmls> <archivo_csv_con_uuids> <carpeta_de_salida>")
        print("Recuerda instalar las dependencias con: pip3 install -r requirements.txt")
        sys.exit(1)
    xmls_path = sys.argv[1]
    uuids_path = sys.argv[2]
    res_path = sys.argv[3]
    main(xmls_path, uuids_path, res_path)
