import os
import sys
import time
import subprocess
import webbrowser

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    smartvessel_dir = os.path.join(base_dir, "SmartVesselAI")
    
    # Auto-detect virtual environment python if present
    venv_candidate = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    venv_python = venv_candidate if os.path.exists(venv_candidate) else sys.executable

    print("=" * 65)
    print("SMARTVESSEL AI - SOFTWARE APPLICATION LAUNCHER")
    print("=" * 65)

    db_path = os.path.join(smartvessel_dir, "smartvessel.db")
    if not os.path.exists(db_path):
        print("[INIT] Database not found. Seeding initial dataset...")
        subprocess.run([venv_python, os.path.join(smartvessel_dir, "ml", "dataset", "seed_data.py")], cwd=smartvessel_dir)

    model_path = os.path.join(base_dir, "models", "freight_model.pkl")
    if not os.path.exists(model_path):
        print("[INIT] Trained model artifact not found. Training model now...")
        subprocess.run([venv_python, os.path.join(base_dir, "train_model.py")], cwd=base_dir)

    print("\nStarting SmartVesselAI Software Engine on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=base_dir
    )

    time.sleep(2)

    url = "http://localhost:8000"
    print("\n" + "=" * 65)
    print(f"[ONLINE] SMARTVESSEL AI SOFTWARE MVP IS ONLINE AT: {url}")
    print("=" * 65)
    print("Press CTRL+C to stop the software server.\n")

    try:
        webbrowser.open(url)
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down SmartVesselAI Software Application...")
        backend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
