"""NT 2022.001 - Consulta GTIN (CCG) via ComunicacaoSefaz.

Only the HTTP transport (``requests.post``) is mocked; the request XML, the SOAP
envelope and the response parsing run for real. Response fixtures follow the
retConsGTIN layout of the NT; the SOAP wrapper element names around it
(ccgConsGTINResponse/nfeResultMsg) are illustrative, which is why the parser
looks for retConsGTIN anywhere in the body.
"""

from pathlib import Path
from unittest import mock

import pytest
import requests

from pynfe.processamento.comunicacao import ComunicacaoSefaz
from pynfe.utils import etree
from pynfe.utils.flags import NAMESPACE_CCG_GTIN, NAMESPACE_NFE, NAMESPACE_SOAP
from pynfe.utils.webservices import CCG_GTIN

FIXTURES = Path(__file__).parent / "fixtures" / "ccg_gtin"
NS = {"soap": NAMESPACE_SOAP, "ccg": NAMESPACE_CCG_GTIN, "nfe": NAMESPACE_NFE}


def _fixture(nome):
    return (FIXTURES / nome).read_bytes()


def _comunicacao(homologacao=False):
    return ComunicacaoSefaz("SP", "./tests/certificado.pfx", b"123456", homologacao=homologacao)


def _consultar(gtin, resposta=b"", homologacao=False, timeout=None):
    con = _comunicacao(homologacao)
    with mock.patch("pynfe.processamento.comunicacao.requests.post") as post:
        post.return_value = mock.Mock(content=resposta)
        result = con.consulta_gtin(gtin, timeout=timeout)
    return con, post, result


def test_posts_to_svrs_ccg_endpoint_with_soap12_action_and_client_cert():
    _, post, _ = _consultar("7891000315507", timeout=5)
    args, kwargs = post.call_args
    assert args[0] == CCG_GTIN
    assert args[0] == "https://dfe-servico.svrs.rs.gov.br/ws/ccgConsGTIN/ccgConsGTIN.asmx"
    content_type = kwargs["headers"]["content-type"]
    assert content_type.startswith("application/soap+xml; charset=utf-8;")
    assert 'action="http://www.portalfiscal.inf.br/nfe/wsdl/ccgConsGtin/ccgConsGTIN"' in (
        content_type
    )
    assert kwargs["timeout"] == 5
    cert, chave = kwargs["cert"]
    assert cert and chave
    assert kwargs["verify"] is False


def test_homologacao_still_uses_the_only_published_endpoint():
    _, post, _ = _consultar("7891000315507", homologacao=True)
    assert post.call_args.args[0] == CCG_GTIN


def test_envelope_wraps_unsigned_consgtin_in_nfedadosmsg():
    _, post, _ = _consultar("7891000315507")
    corpo = post.call_args.args[1]
    assert corpo.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    raiz = etree.fromstring(corpo.encode("utf-8"))
    cons = raiz.find("soap:Body/ccg:ccgConsGTIN/ccg:nfeDadosMsg/nfe:consGTIN", namespaces=NS)
    assert cons is not None
    assert cons.get("versao") == "1.00"
    assert [filho.tag for filho in cons] == ["{%s}GTIN" % NAMESPACE_NFE]
    assert cons.find("nfe:GTIN", namespaces=NS).text == "7891000315507"
    assert raiz.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature") is None


def test_other_sefaz_calls_keep_the_default_headers():
    con = _comunicacao()
    with mock.patch("pynfe.processamento.comunicacao.requests.post") as post:
        con._post("https://sefaz.example/ws", etree.Element("NFe"))
    assert post.call_args.kwargs["headers"] == con._post_header()


@pytest.mark.parametrize("gtin", ["12345678", "012345678905", "7891000315507", "17891000315504"])
def test_accepts_every_gtin_length_from_the_nt(gtin):
    _, post, _ = _consultar(gtin)
    assert "<GTIN>%s</GTIN>" % gtin in post.call_args.args[1]


@pytest.mark.parametrize("gtin", ["", "1234567", "123456789", "78910003155X7", "SEM GTIN"])
def test_rejects_malformed_gtin_without_calling_sefaz(gtin):
    con = _comunicacao()
    with mock.patch("pynfe.processamento.comunicacao.requests.post") as post:
        with pytest.raises(ValueError):
            con.consulta_gtin(gtin)
    post.assert_not_called()


@pytest.mark.parametrize(
    "erro",
    [
        requests.exceptions.ConnectTimeout("timed out"),
        requests.exceptions.ConnectionError("connection reset"),
        requests.exceptions.SSLError("handshake failure"),
    ],
)
def test_transport_error_propagates_and_removes_the_temporary_cert_files(erro):
    con = _comunicacao()
    with mock.patch("pynfe.processamento.comunicacao.requests.post", side_effect=erro) as post:
        with pytest.raises(type(erro)):
            con.consulta_gtin("7891000315507", timeout=5)
    post.assert_called_once()
    cert, chave = post.call_args.kwargs["cert"]
    assert not Path(cert).exists()
    assert not Path(chave).exists()


def test_reads_found_product():
    _, _, resposta = _consultar("7891000315507", _fixture("encontrado.xml"))
    assert ComunicacaoSefaz.ler_retorno_consulta_gtin(resposta.content) == {
        "cStat": "9490",
        "xMotivo": "Consulta realizada com sucesso",
        "verAplic": "RS20220531",
        "dhResp": "2026-11-24T13:00:00-03:00",
        "GTIN": "7891000315507",
        "tpGTIN": "13",
        "xProd": "LEITE CONDENSADO 395G",
        "NCM": "04029900",
        "CEST": ["1702000"],
    }


def test_reads_not_found_without_product_data():
    retorno = ComunicacaoSefaz.ler_retorno_consulta_gtin(_fixture("inexistente.xml"))
    assert retorno["cStat"] == "9494"
    assert retorno["xMotivo"].startswith("Rejeição: GTIN inexistente")
    assert retorno["xProd"] is None
    assert retorno["NCM"] is None
    assert retorno["CEST"] == []


def test_reads_brand_owner_not_authorized_without_product_data():
    retorno = ComunicacaoSefaz.ler_retorno_consulta_gtin(_fixture("nao_autorizado.xml"))
    assert retorno["cStat"] == "9496"
    assert retorno["GTIN"] == "7891000315507"
    assert retorno["xProd"] is None


def test_reads_certificate_not_an_issuer():
    retorno = ComunicacaoSefaz.ler_retorno_consulta_gtin(_fixture("certificado_nao_emitente.xml"))
    assert retorno["cStat"] == "9493"
    assert retorno["GTIN"] is None


def test_reader_accepts_text_bodies():
    texto = _fixture("encontrado.xml").decode("utf-8")
    assert ComunicacaoSefaz.ler_retorno_consulta_gtin(texto)["cStat"] == "9490"


@pytest.mark.parametrize(
    "corpo",
    [
        b"",
        b"<html><title>403 - Forbidden: Access is denied.</title></html>",
        b'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body>'
        b"<soap:Fault><soap:Reason><soap:Text>erro</soap:Text></soap:Reason></soap:Fault>"
        b"</soap:Body></soap:Envelope>",
    ],
)
def test_reader_raises_value_error_without_retconsgtin(corpo):
    with pytest.raises(ValueError):
        ComunicacaoSefaz.ler_retorno_consulta_gtin(corpo)
