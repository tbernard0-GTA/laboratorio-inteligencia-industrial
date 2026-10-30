import unittest

from catalogo_tags import CATALOGO, ler_tags


class SimuladorDeTeste:
    def __init__(self):
        self.nomes_medidas = [t.descricao for t in CATALOGO if t.categoria == "medicao"]
        self.nomes_manipuladas = [t.descricao for t in CATALOGO if t.categoria == "manipulada"]
        self.medidas = list(range(41))
        self.manipuladas = list(range(100, 112))

    def get_measurement_names(self):
        return self.nomes_medidas

    def get_mv_names(self):
        return self.nomes_manipuladas

    def get_measurements(self):
        return self.medidas

    def get_manipulated_vars(self):
        return self.manipuladas


class CatalogoTest(unittest.TestCase):
    def test_quantidades_identificadores_e_indices(self):
        self.assertEqual(len(CATALOGO), 53)
        self.assertEqual(len({t.identificador for t in CATALOGO}), 53)
        for categoria, prefixo, tamanho in (("medicao", "XMEAS", 41), ("manipulada", "XMV", 12)):
            tags = [t for t in CATALOGO if t.categoria == categoria]
            self.assertEqual([t.indice for t in tags], list(range(tamanho)))
            self.assertEqual([t.identificador for t in tags], [f"{prefixo}({i})" for i in range(1, tamanho + 1)])
            self.assertTrue(all(t.descricao and t.unidade for t in tags))

    def test_correspondencia_de_todos_os_indices(self):
        valores = ler_tags(SimuladorDeTeste())
        self.assertEqual(valores, {**{f"XMEAS({i + 1})": float(i) for i in range(41)},
                                   **{f"XMV({i + 1})": float(100 + i) for i in range(12)}})

    def test_ordem_ou_tamanho_incompativel_rejeitados(self):
        for atributo in ("nomes_medidas", "nomes_manipuladas"):
            sim = SimuladorDeTeste()
            nomes = getattr(sim, atributo)
            nomes[0], nomes[1] = nomes[1], nomes[0]
            with self.subTest(atributo=atributo), self.assertRaises(ValueError):
                ler_tags(sim)
        for atributo in ("medidas", "manipuladas"):
            sim = SimuladorDeTeste()
            getattr(sim, atributo).pop()
            with self.subTest(atributo=atributo), self.assertRaises(ValueError):
                ler_tags(sim)

    def test_unidades_e_pontos_de_referencia(self):
        tags = {t.identificador: t for t in CATALOGO}
        self.assertEqual((tags["XMEAS(7)"].descricao, tags["XMEAS(7)"].unidade), ("Reactor Pressure", "kPa(g)"))
        self.assertEqual((tags["XMEAS(8)"].descricao, tags["XMEAS(8)"].unidade), ("Reactor Level", "%"))
        self.assertEqual((tags["XMEAS(9)"].descricao, tags["XMEAS(9)"].unidade), ("Reactor Temperature", "deg C"))
        self.assertEqual(tags["XMEAS(23)"].descricao, "Reactor Feed Component A")
        self.assertEqual(tags["XMEAS(41)"].descricao, "Product Component H")
        self.assertEqual(tags["XMV(1)"].descricao, "D Feed Flow (stream 2)")
        self.assertEqual(tags["XMV(12)"].descricao, "Agitator Speed")
        self.assertTrue(all(t.unidade == "mol%" for t in CATALOGO[22:41]))
        self.assertTrue(all(t.unidade == "%" for t in CATALOGO[41:]))


class IntegracaoTEPTest(unittest.TestCase):
    def test_simulador_real(self):
        try:
            from tep import TEPSimulator
            from tep.constants import MEASUREMENT_UNITS
        except ImportError:
            self.skipTest("biblioteca tep não instalada")
        sim = TEPSimulator(backend="python", random_seed=1234)
        sim.initialize()
        valores = ler_tags(sim)
        medidas, manipuladas = sim.get_measurements(), sim.get_manipulated_vars()
        self.assertEqual(len(valores), 53)
        unidades = ["kPa(g)" if i in (6, 12, 15) else unidade
                    for i, unidade in enumerate(MEASUREMENT_UNITS)]
        self.assertEqual([tag.unidade for tag in CATALOGO[:41]], unidades)
        for tag in CATALOGO:
            vetor = medidas if tag.categoria == "medicao" else manipuladas
            self.assertEqual(valores[tag.identificador], float(vetor[tag.indice]))


if __name__ == "__main__":
    unittest.main()
