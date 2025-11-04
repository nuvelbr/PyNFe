#!/usr/bin/env python
# *-* encoding: utf8 *-*
"""
Testes para QR-Code versão 3 da NFC-e (NT 2025.001)

Este módulo testa a geração do QR-Code v3 que elimina o uso de CSC
e implementa dois modos:
- Online (tpEmis=1): chave|3|tpAmb (sem assinatura)
- Offline (tpEmis=9): chave|3|tpAmb|dia|vNF|tp_idDest|idDest|ASSINATURA
"""

import datetime
import unittest
from decimal import Decimal

from pynfe.entidades.cliente import Cliente
from pynfe.entidades.emitente import Emitente
from pynfe.entidades.fonte_dados import _fonte_dados
from pynfe.entidades.notafiscal import NotaFiscal
from pynfe.entidades.produto import Produto
from pynfe.processamento.assinatura import AssinaturaA1
from pynfe.processamento.serializacao import SerializacaoQrcode, SerializacaoXML
from pynfe.utils.flags import CODIGO_BRASIL, NAMESPACE_NFE


class QrCodeV3TestCase(unittest.TestCase):
    """Testes para o QR-Code versão 3 da NFC-e"""

    def setUp(self):
        self.certificado = "./tests/certificado.pfx"
        self.senha = bytes("123456", "utf-8")
        self.uf = "PR"
        self.homologacao = True

        self.ns = {"ns": NAMESPACE_NFE}

        # Limpa fonte de dados
        _fonte_dados._objetos = []

    def tearDown(self):
        _fonte_dados._objetos = []

    def preenche_emitente(self):
        emitente = Emitente(
            razao_social="NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL",
            nome_fantasia="Nome Fantasia da Empresa",
            cnpj="99999999000199",
            codigo_de_regime_tributario="3",
            inscricao_estadual="9999999999",
            inscricao_municipal="12345",
            cnae_fiscal="9999999",
            endereco_logradouro="Rua da Paz",
            endereco_numero="666",
            endereco_bairro="Sossego",
            endereco_municipio="Paranavaí",
            endereco_uf="PR",
            endereco_cep="87704000",
            endereco_pais=CODIGO_BRASIL,
        )
        return emitente

    def preenche_cliente_cpf(self):
        cliente = Cliente(
            razao_social="JOSE DA SILVA",
            tipo_documento="CPF",
            numero_documento="12345678901",
            indicador_ie=9,
            endereco_logradouro="Rua dos Bobos",
            endereco_numero="Zero",
            endereco_bairro="Aquele Mesmo",
            endereco_municipio="Brasilia",
            endereco_uf="DF",
            endereco_cep="12345123",
            endereco_pais=CODIGO_BRASIL,
        )
        return cliente

    def preenche_cliente_cnpj(self):
        cliente = Cliente(
            razao_social="EMPRESA TESTE LTDA",
            tipo_documento="CNPJ",
            numero_documento="12345678000199",
            indicador_ie=1,
            inscricao_estadual="123456789",
            endereco_logradouro="Rua Comercial",
            endereco_numero="100",
            endereco_bairro="Centro",
            endereco_municipio="Brasilia",
            endereco_uf="DF",
            endereco_cep="12345123",
            endereco_pais=CODIGO_BRASIL,
        )
        return cliente

    def preenche_produto(self):
        produto = Produto(
            codigo="123456",
            descricao="PRODUTO TESTE",
            ncm="99999999",
            cfop="5102",
            unidade_comercial="UN",
            quantidade_comercial=Decimal("1.0000"),
            valor_unitario_comercial=Decimal("50.00"),
            valor_total_bruto=Decimal("50.00"),
            unidade_tributavel="UN",
            quantidade_tributavel=Decimal("1.0000"),
            valor_unitario_tributavel=Decimal("50.00"),
            ind_total=1,
            icms_modalidade="102",
            icms_origem=0,
            icms_csosn="102",
            pis_modalidade="07",
            cofins_modalidade="07",
        )
        return produto

    def cria_nfce_online(self, cliente=None, uf="PR"):
        """Cria uma NFC-e em modo online (tpEmis=1)"""
        # Municípios por UF para ajustar emitente
        municipios_por_uf = {
            "PR": "Paranavaí",
            "SP": "São Paulo",
            "BA": "Salvador",
            "MG": "Belo Horizonte",
            "PB": "João Pessoa",
        }

        emitente = self.preenche_emitente()
        emitente.endereco_uf = uf
        emitente.endereco_municipio = municipios_por_uf.get(uf, "Paranavaí")

        utc = datetime.timezone.utc
        data_emissao = datetime.datetime(2025, 1, 14, 12, 0, 0, tzinfo=utc)
        data_saida = datetime.datetime(2025, 1, 14, 13, 10, 20, tzinfo=utc)

        # Código IBGE por UF (simplificado para testes)
        codigos_ibge = {
            "PR": "4118402",  # Paranavaí
            "SP": "3550308",  # São Paulo
            "BA": "2927408",  # Salvador
            "MG": "3106200",  # Belo Horizonte
            "PB": "2507507",  # João Pessoa
        }

        notafiscal = NotaFiscal(
            emitente=emitente,
            cliente=cliente,
            uf=uf,
            natureza_operacao="VENDA",
            modelo=65,  # NFC-e
            serie="1",
            numero_nf="111",
            data_emissao=data_emissao,
            data_saida_entrada=data_saida,
            tipo_documento=1,
            municipio=codigos_ibge.get(uf, "4118402"),
            tipo_impressao_danfe=4,  # NFC-e
            forma_emissao="1",  # Normal (online)
            cliente_final=1,
            indicador_destino=1,
            indicador_presencial=1,
            finalidade_emissao="1",
            processo_emissao="0",
            transporte_modalidade_frete=9,
            informacoes_adicionais_interesse_fisco="Mensagem complementar",
            totais_tributos_aproximado=Decimal("10.00"),
        )

        # Adiciona produto
        notafiscal.adicionar_produto_servico(
            codigo="123456",
            descricao="PRODUTO TESTE",
            ncm="99999999",
            cfop="5102",
            unidade_comercial="UN",
            quantidade_comercial=Decimal("1.0000"),
            valor_unitario_comercial=Decimal("50.00"),
            valor_total_bruto=Decimal("50.00"),
            unidade_tributavel="UN",
            quantidade_tributavel=Decimal("1.0000"),
            valor_unitario_tributavel=Decimal("50.00"),
            ind_total=1,
            icms_modalidade="102",
            icms_origem=0,
            icms_csosn="102",
            pis_modalidade="07",
            cofins_modalidade="07",
            valor_tributos_aprox="5.00",
        )

        # Adiciona pagamento
        notafiscal.adicionar_pagamento(
            t_pag="01", x_pag="Dinheiro", v_pag=Decimal("50.00"), ind_pag=0
        )

        return notafiscal

    def cria_nfce_offline(self, cliente=None, uf="PR"):
        """Cria uma NFC-e em modo offline/contingência (tpEmis=9)"""
        emitente = self.preenche_emitente()
        emitente.endereco_uf = uf

        utc = datetime.timezone.utc
        data_emissao = datetime.datetime(2025, 1, 14, 12, 0, 0, tzinfo=utc)
        data_saida = datetime.datetime(2025, 1, 14, 13, 10, 20, tzinfo=utc)

        codigos_ibge = {
            "PR": "4118402",
            "SP": "3550308",
            "BA": "2927408",
            "MG": "3106200",
            "PB": "2507507",
        }

        notafiscal = NotaFiscal(
            emitente=emitente,
            cliente=cliente,
            uf=uf,
            natureza_operacao="VENDA",
            modelo=65,
            serie="1",
            numero_nf="111",
            data_emissao=data_emissao,
            data_saida_entrada=data_saida,
            tipo_documento=1,
            municipio=codigos_ibge.get(uf, "4118402"),
            tipo_impressao_danfe=4,
            forma_emissao="9",  # Contingência offline
            cliente_final=1,
            indicador_destino=1,
            indicador_presencial=1,
            finalidade_emissao="1",
            processo_emissao="0",
            transporte_modalidade_frete=9,
            informacoes_adicionais_interesse_fisco="Mensagem complementar",
            totais_tributos_aproximado=Decimal("10.00"),
        )

        # Adiciona produto
        notafiscal.adicionar_produto_servico(
            codigo="123456",
            descricao="PRODUTO TESTE",
            ncm="99999999",
            cfop="5102",
            unidade_comercial="UN",
            quantidade_comercial=Decimal("1.0000"),
            valor_unitario_comercial=Decimal("50.00"),
            valor_total_bruto=Decimal("50.00"),
            unidade_tributavel="UN",
            quantidade_tributavel=Decimal("1.0000"),
            valor_unitario_tributavel=Decimal("50.00"),
            ind_total=1,
            icms_modalidade="102",
            icms_origem=0,
            icms_csosn="102",
            pis_modalidade="07",
            cofins_modalidade="07",
            valor_tributos_aprox="5.00",
        )

        # Adiciona pagamento
        notafiscal.adicionar_pagamento(
            t_pag="01", x_pag="Dinheiro", v_pag=Decimal("50.00"), ind_pag=0
        )

        return notafiscal

    def test_qrcode_v3_online_sem_cliente(self):
        """Testa geração de QR-Code v3 em modo online sem cliente"""
        _notafiscal = self.cria_nfce_online(cliente=None, uf="PR")

        # Serializa e assina
        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        # Gera QR-Code v3
        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(xml_assinado, return_qr=True)

        # Verifica estrutura do QR-Code
        self.assertIsNotNone(qrcode_url)
        self.assertIn("?p=", qrcode_url)

        # Extrai payload
        payload = qrcode_url.split("?p=")[1]

        # Verifica formato: chave|3|tpAmb (3 campos no modo online)
        campos = payload.split("|")
        self.assertEqual(len(campos), 3, "QR-Code online deve ter 3 campos")
        self.assertEqual(campos[1], "3", "Segunda posição deve ser versão 3")
        self.assertEqual(campos[2], "2", "Terceira posição deve ser tpAmb=2 (homologação)")
        self.assertEqual(len(campos[0]), 44, "Chave de acesso deve ter 44 dígitos")

    def test_qrcode_v3_online_com_cpf(self):
        """Testa geração de QR-Code v3 em modo online com cliente CPF"""
        cliente = self.preenche_cliente_cpf()
        _notafiscal = self.cria_nfce_online(cliente=cliente, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(xml_assinado, return_qr=True)

        # Verifica estrutura
        self.assertIn("?p=", qrcode_url)
        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        # Modo online: não inclui dados do cliente no QR-Code
        self.assertEqual(len(campos), 3)
        self.assertEqual(campos[1], "3")

    def test_qrcode_v3_online_com_cnpj(self):
        """Testa geração de QR-Code v3 em modo online com cliente CNPJ"""
        cliente = self.preenche_cliente_cnpj()
        _notafiscal = self.cria_nfce_online(cliente=cliente, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(xml_assinado, return_qr=True)

        # Verifica estrutura
        self.assertIn("?p=", qrcode_url)
        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        self.assertEqual(len(campos), 3)
        self.assertEqual(campos[1], "3")

    def test_qrcode_v3_offline_sem_cliente(self):
        """Testa geração de QR-Code v3 em modo offline sem cliente"""
        _notafiscal = self.cria_nfce_offline(cliente=None, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        # Função de assinatura para o QR-Code
        def assinar_payload(payload):
            return assinador.assinar_qrcode_v3(payload)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(
            xml_assinado, assinatura_function=assinar_payload, return_qr=True
        )

        # Verifica estrutura
        self.assertIn("?p=", qrcode_url)
        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        # Modo offline: chave|3|tpAmb|dia|vNF|tp_idDest|idDest|ASSINATURA (8 campos)
        self.assertEqual(len(campos), 8, "QR-Code offline deve ter 8 campos")
        self.assertEqual(campos[1], "3", "Segunda posição deve ser versão 3")
        self.assertEqual(campos[2], "2", "Terceira posição deve ser tpAmb=2")
        self.assertEqual(campos[3], "14", "Quarta posição deve ser dia=14")
        self.assertEqual(campos[4], "50.00", "Quinta posição deve ser vNF=50.00")
        self.assertEqual(campos[5], "", "Sexta posição deve estar vazia (sem tp_idDest)")
        self.assertEqual(campos[6], "", "Sétima posição deve estar vazia (sem idDest)")
        self.assertGreater(len(campos[7]), 0, "Oitava posição deve conter assinatura")

    def test_qrcode_v3_offline_com_cpf(self):
        """Testa geração de QR-Code v3 em modo offline com cliente CPF"""
        cliente = self.preenche_cliente_cpf()
        _notafiscal = self.cria_nfce_offline(cliente=cliente, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        def assinar_payload(payload):
            return assinador.assinar_qrcode_v3(payload)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(
            xml_assinado, assinatura_function=assinar_payload, return_qr=True
        )

        # Verifica estrutura
        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        self.assertEqual(len(campos), 8)
        self.assertEqual(campos[5], "2", "tp_idDest deve ser 2 para CPF")
        self.assertEqual(campos[6], "12345678901", "idDest deve ser o CPF")
        self.assertGreater(len(campos[7]), 0, "Deve conter assinatura")

    def test_qrcode_v3_offline_com_cnpj(self):
        """Testa geração de QR-Code v3 em modo offline com cliente CNPJ"""
        cliente = self.preenche_cliente_cnpj()
        _notafiscal = self.cria_nfce_offline(cliente=cliente, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        def assinar_payload(payload):
            return assinador.assinar_qrcode_v3(payload)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(
            xml_assinado, assinatura_function=assinar_payload, return_qr=True
        )

        # Verifica estrutura
        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        self.assertEqual(len(campos), 8)
        self.assertEqual(campos[5], "1", "tp_idDest deve ser 1 para CNPJ")
        self.assertEqual(campos[6], "12345678000199", "idDest deve ser o CNPJ")
        self.assertGreater(len(campos[7]), 0, "Deve conter assinatura")

    def test_qrcode_v3_offline_sem_assinatura_deve_falhar(self):
        """Testa que QR-Code v3 offline sem função de assinatura deve falhar"""
        _notafiscal = self.cria_nfce_offline(cliente=None, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        qrcode_gen = SerializacaoQrcode()

        # Deve lançar ValueError se não fornecer assinatura_function
        with self.assertRaises(ValueError) as context:
            qrcode_gen.gerar_qrcode_v3(xml_assinado, assinatura_function=None)

        self.assertIn("assinatura_function é obrigatória", str(context.exception))

    def test_qrcode_v3_diferentes_ufs(self):
        """Testa geração de QR-Code v3 para diferentes UFs"""
        ufs_testar = ["PR", "SP", "BA", "MG"]

        for uf in ufs_testar:
            with self.subTest(uf=uf):
                _notafiscal = self.cria_nfce_online(cliente=None, uf=uf)

                serializador = SerializacaoXML(_fonte_dados, homologacao=True)
                xml = serializador.exportar()

                assinador = AssinaturaA1(self.certificado, self.senha)
                xml_assinado = assinador.assinar(xml)

                qrcode_gen = SerializacaoQrcode()
                xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(xml_assinado, return_qr=True)

                # Verifica que URL foi gerada
                self.assertIsNotNone(qrcode_url)
                self.assertIn("?p=", qrcode_url)

                # Limpa para próximo teste
                _fonte_dados._objetos = []

    def test_qrcode_v3_infnfesupl_inserido(self):
        """Testa que infNFeSupl é inserido corretamente no XML"""
        _notafiscal = self.cria_nfce_online(cliente=None, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr = qrcode_gen.gerar_qrcode_v3(xml_assinado)

        # Verifica que infNFeSupl existe
        infnfesupl = xml_com_qr.xpath("infNFeSupl")
        self.assertEqual(len(infnfesupl), 1, "Deve existir exatamente um infNFeSupl")

        # Verifica que contém qrCode e urlChave
        qrcode_elements = xml_com_qr.xpath("infNFeSupl/qrCode")
        urlchave_elements = xml_com_qr.xpath("infNFeSupl/urlChave")

        self.assertEqual(len(qrcode_elements), 1, "Deve existir qrCode")
        self.assertEqual(len(urlchave_elements), 1, "Deve existir urlChave")

        # Verifica que qrCode não está vazio
        qrcode_text = qrcode_elements[0].text
        self.assertIsNotNone(qrcode_text)
        self.assertGreater(len(qrcode_text), 0)

    def test_qrcode_v3_formato_decimal_vnf(self):
        """Testa que vNF é formatado corretamente com 2 casas decimais"""
        cliente = self.preenche_cliente_cpf()
        _notafiscal = self.cria_nfce_offline(cliente=cliente, uf="PR")

        serializador = SerializacaoXML(_fonte_dados, homologacao=True)
        xml = serializador.exportar()

        assinador = AssinaturaA1(self.certificado, self.senha)
        xml_assinado = assinador.assinar(xml)

        def assinar_payload(payload):
            return assinador.assinar_qrcode_v3(payload)

        qrcode_gen = SerializacaoQrcode()
        xml_com_qr, qrcode_url = qrcode_gen.gerar_qrcode_v3(
            xml_assinado, assinatura_function=assinar_payload, return_qr=True
        )

        payload = qrcode_url.split("?p=")[1]
        campos = payload.split("|")

        # Verifica formato do vNF (campo 4, índice 4)
        vnf = campos[4]
        self.assertRegex(vnf, r"^\d+\.\d{2}$", "vNF deve ter formato XX.XX")
        self.assertEqual(vnf, "50.00")


if __name__ == "__main__":
    unittest.main()
