"""Testes locais da configuração de rede, sem dependências de aplicação."""

import os
import unittest
from unittest.mock import patch

from servidor_opc import configurar_endpoint


class ConfiguracaoEndpointTest(unittest.TestCase):
    def test_valores_padrao(self):
        config = configurar_endpoint({})
        self.assertEqual(config.bind_host, "192.168.1.19")
        self.assertEqual(config.port, 4840)
        self.assertEqual(config.endpoint, "opc.tcp://192.168.1.19:4840/tep/")

    def test_bind_e_anuncio_independentes(self):
        config = configurar_endpoint({
            "OPC_UA_BIND_HOST": "0.0.0.0",
            "OPC_UA_ADVERTISE_HOST": "10.77.0.10",
            "OPC_UA_PORT": "14840",
        })
        self.assertEqual(config.bind_host, "0.0.0.0")
        self.assertEqual(config.port, 14840)
        self.assertEqual(config.endpoint, "opc.tcp://10.77.0.10:14840/tep/")

    def test_nome_de_host_e_porta_padrao(self):
        config = configurar_endpoint({
            "OPC_UA_BIND_HOST": "127.0.0.1",
            "OPC_UA_ADVERTISE_HOST": "pi4.local",
        })
        self.assertEqual(config.bind_host, "127.0.0.1")
        self.assertEqual(config.port, 4840)
        self.assertEqual(config.endpoint, "opc.tcp://pi4.local:4840/tep/")

    def test_entradas_vazias_ou_invalidas(self):
        casos = [
            {"OPC_UA_BIND_HOST": ""},
            {"OPC_UA_ADVERTISE_HOST": ""},
            {"OPC_UA_ADVERTISE_HOST": "0.0.0.0"},
            {"OPC_UA_PORT": ""},
            {"OPC_UA_PORT": "abc"},
            {"OPC_UA_PORT": "0"},
            {"OPC_UA_PORT": "65536"},
        ]
        for ambiente in casos:
            with self.subTest(ambiente=ambiente):
                with self.assertRaises(ValueError):
                    configurar_endpoint(ambiente)

    def test_nao_modifica_ambiente_do_processo(self):
        with patch.dict(os.environ, {"OPC_UA_PORT": "1234"}, clear=True):
            anterior = dict(os.environ)
            configurar_endpoint({"OPC_UA_PORT": "4841"})
            self.assertEqual(dict(os.environ), anterior)

    def test_le_ambiente_do_processo_sem_parametro(self):
        anterior = dict(os.environ)
        with patch.dict(os.environ, {
            "OPC_UA_BIND_HOST": "0.0.0.0",
            "OPC_UA_ADVERTISE_HOST": "pi4.local",
            "OPC_UA_PORT": "14840",
        }, clear=True):
            config = configurar_endpoint()
            self.assertEqual(config.bind_host, "0.0.0.0")
            self.assertEqual(config.port, 14840)
            self.assertEqual(config.endpoint, "opc.tcp://pi4.local:14840/tep/")
        self.assertEqual(dict(os.environ), anterior)


if __name__ == "__main__":
    unittest.main()
