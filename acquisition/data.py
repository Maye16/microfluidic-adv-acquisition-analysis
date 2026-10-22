import numpy as np
import matplotlib.pyplot as plt

def load_and_plot_signals(filename):
    """
    Charge les données depuis un fichier .npy et affiche un exemple de signal.

    Args:
        filename (str): Chemin vers le fichier .npy contenant les signaux.
    """
    # Charger les données depuis le fichier .npy
    signals = np.load(filename, allow_pickle=True)

    # Afficher le nombre total de signaux
    print(f"Nombre total de signaux: {signals.shape[0]}")

    # Parcourir chaque signal
    for i in range(signals.shape[0]):
        signal = signals[i]
        times = signal[:, 0]  # Première colonne : temps
        voltages = signal[:, 1]  # Deuxième colonne : tensions
        print(f"Signal {i + 1}: {len(times)} points, Tension min: {voltages.min():.3f} V, Tension max: {voltages.max():.3f} V")

    # Tracer un exemple de signal (par exemple, le premier signal)
    i = 99
    if signals.shape[0] > 0:
        times, voltages = signals[i, :, 0], signals[i, :, 1]
        plt.figure(figsize=(10, 6))
        plt.plot(times, voltages, label=f"Signal {i}")
        plt.xlabel("Temps (s)")
        plt.ylabel("Tension (V)")
        plt.title("Exemple de signal enregistré")
        plt.grid(True)
        plt.legend()
        plt.show()
    else:
        print("Aucun signal à afficher.")

# Exemple d'utilisation
if __name__ == "__main__":
    raise SystemExit(
        "Specify an authorized .npy file and call load_and_plot_signals(path) explicitly; "
        "the hard-coded laboratory test path was intentionally disabled."
    )
