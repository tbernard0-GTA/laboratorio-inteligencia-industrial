from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]

def test_compose_security_and_contract():
    data = yaml.safe_load((ROOT / 'docker/compose.yaml').read_text())
    assert set(data['services']) == {'tep-opc', 'streamlit'}
    for service in data['services'].values():
        assert service['restart'] == 'unless-stopped'
        assert not service.get('privileged', False)
        assert 'network_mode' not in service
        assert all(p.startswith('${PI4_BIND_IP:') for p in service['ports'])
        assert service['cap_drop'] == ['ALL']
        assert 'healthcheck' in service
    assert data['services']['streamlit']['environment']['OPC_ENDPOINT'] == 'opc.tcp://tep-opc:4840/tep/'

def test_original_lessons_unchanged():
    source = (ROOT.parent / 'aula-01/servidor_opc.py').read_text()
    assert '192.168.1.19' in source
    assert 'socket_address' not in source


def test_streamlit_is_explicit_complement():
    data = yaml.safe_load((ROOT / "docker/compose.yaml").read_text())
    assert "profiles" not in data["services"]["tep-opc"]
    assert data["services"]["streamlit"]["profiles"] == ["complemento"]
