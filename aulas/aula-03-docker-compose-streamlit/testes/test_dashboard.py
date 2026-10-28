"""AppTest com coletor explicitamente simulado para validar a apresentacao."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'streamlit'))
import collector
from streamlit.testing.v1 import AppTest

class FakeCollector:
    error = None
    age = 0
    def __init__(self, *args):
        pass
    def snapshot(self):
        now = (datetime.now(timezone.utc) - timedelta(seconds=self.age)).isoformat()
        return [{"received_at": now, "values": {n: {"value": v, "unit": u, "timestamp": now, "quality": "Good"} for n,v,u in [('Pressao',2705.,'kPa(g)'),('Nivel',74.7,'%'),('Temperatura',120.3,'C')]}}], self.error

def test_dashboard_metrics_and_trends(monkeypatch):
    monkeypatch.setattr(collector, 'Collector', FakeCollector)
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit/app.py')).run(timeout=15)
    assert not at.exception
    assert len(at.metric) == 3
    assert at.success

def test_dashboard_does_not_present_stale_as_current(monkeypatch):
    class StaleCollector(FakeCollector):
        age = 60
        error = 'Servidor indisponivel (teste)'
    monkeypatch.setattr(collector, 'Collector', StaleCollector)
    import streamlit as st
    st.cache_resource.clear()
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'streamlit/app.py')).run(timeout=15)
    assert not at.exception
    assert len(at.metric) == 0
    assert at.error
    st.cache_resource.clear()
