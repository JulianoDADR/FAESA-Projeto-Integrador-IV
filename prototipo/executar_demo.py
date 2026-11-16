"""Um comando para a demonstracao: treina se faltar o modelo e sobe o servidor em http://localhost:8000."""
import subprocess
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent
if not (raiz / "ml" / "saida" / "modelo.pkl").exists():
    print("Modelo não encontrado: treinando...")
    subprocess.run([sys.executable, str(raiz / "ml" / "treinar.py"), "--salvar"], check=True, cwd=raiz)
print("Abra http://localhost:8000")
subprocess.run([sys.executable, "-m", "uvicorn", "app.principal:app", "--port", "8000"], cwd=raiz)
