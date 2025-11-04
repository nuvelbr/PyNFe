# -*- coding: utf-8 -*-
import base64
from typing import Union

import signxml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from pynfe.entidades import CertificadoA1
from pynfe.utils import CustomXMLSigner, etree, remover_acentos


class Assinatura(object):
    """Classe abstrata responsavel por definir os metodos e logica das classes
    de assinatura digital."""

    certificado = None
    senha = None

    def __init__(self, certificado, senha, autorizador=None):
        self.certificado = certificado
        self.senha = senha
        self.autorizador = autorizador

    def assinar(self, xml):
        """Efetua a assinatura da nota"""
        pass


class AssinaturaA1(Assinatura):
    def __init__(self, certificado, senha):
        self.key, self.cert = CertificadoA1(certificado).separar_arquivo(senha)

    def assinar(self, xml: etree._Element, retorna_string=False) -> Union[str, etree._Element]:
        # busca tag que tem id(reference_uri), logo nao importa se tem namespace
        reference = xml.find(".//*[@Id]").attrib["Id"]

        # retira acentos
        xml_str = remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False))
        xml = etree.fromstring(xml_str)

        signer = CustomXMLSigner(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm="sha1",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        signer.excise_empty_xmlns_declarations = True

        ns = {None: signer.namespaces["ds"]}
        signer.namespaces = ns

        ref_uri = ("#%s" % reference) if reference else None
        signed_root = signer.sign(xml, key=self.key, cert=self.cert, reference_uri=ref_uri)
        if retorna_string:
            return etree.tostring(signed_root, encoding="unicode", pretty_print=False)
        else:
            return signed_root

    def assinar_qrcode_v3(self, payload: str) -> str:
        """
        Assina o payload do QR-Code v3 offline usando RSA-SHA1 (NT 2025.001).

        Este método é usado para gerar a assinatura necessária para o QR-Code v3
        em modo offline (contingência, tpEmis=9). A assinatura é feita usando
        o mesmo certificado A1 que assina a NFC-e.

        Args:
            payload: String com os campos do QR-Code concatenados com "|"
                    Formato: chave|3|tpAmb|dia|vNF|tp_idDest|idDest

        Returns:
            Assinatura em Base64 (string)

        Exemplo:
            >>> assinador = AssinaturaA1("certificado.pfx", b"senha")
            >>> payload = "35210299999999000199650010000001111000001112|3|2|14|50.00|2|12345678901"
            >>> assinatura = assinador.assinar_qrcode_v3(payload)
            >>> print(assinatura)  # Retorna string Base64
        """
        # Se self.key for bytes, deserializa para objeto de chave privada
        if isinstance(self.key, bytes):
            private_key = serialization.load_pem_private_key(
                self.key, password=None, backend=default_backend()
            )
        else:
            private_key = self.key

        # Assina usando RSA-SHA1 conforme especificação NT 2025.001
        signature = private_key.sign(
            payload.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA1(),  # SHA1 conforme exigência do manual
        )
        return base64.b64encode(signature).decode("ascii")
