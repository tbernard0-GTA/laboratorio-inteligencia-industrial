import time
from datetime import datetime, timezone
from tep import TEPSimulator

sim = TEPSimulator(backend="python", random_seed=1234)
sim.initialize()

print("Simulação iniciada. Ctrl+C para parar.", flush=True)
try:
    while True:
        inicio = time.monotonic()
        if not sim.step():
            raise RuntimeError("O modelo interrompeu a simulação.")
        medidas = sim.get_measurements()
        horario = datetime.now(timezone.utc).isoformat()
        print(
            f"{horario} | t_modelo={sim.time * 3600:.1f}s | "
            f"pressao={medidas[6]:.2f} kPa(g) | "
            f"nivel={medidas[7]:.2f}% | "
            f"temperatura={medidas[8]:.2f} C",
            flush=True,
        )
        time.sleep(max(0.0, 1.0 - (time.monotonic() - inicio)))
except KeyboardInterrupt:
    print("\nSimulação encerrada.")
