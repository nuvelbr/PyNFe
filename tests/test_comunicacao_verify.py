import pytest

from pynfe.processamento.comunicacao import ComunicacaoCTe, ComunicacaoMDFe, ComunicacaoSefaz


@pytest.mark.parametrize("cls", [ComunicacaoSefaz, ComunicacaoMDFe, ComunicacaoCTe])
def test_verify_default_preserves_legacy_behavior(cls):
    assert cls("SP", "cert.pfx", "x").verify is False


@pytest.mark.parametrize("cls", [ComunicacaoSefaz, ComunicacaoMDFe, ComunicacaoCTe])
def test_verify_is_configurable(cls):
    assert (
        cls("SP", "cert.pfx", "x", verify="/etc/ssl/icp-brasil.pem").verify
        == "/etc/ssl/icp-brasil.pem"
    )
    assert cls("SP", "cert.pfx", "x", verify=True).verify is True
