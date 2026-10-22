# Legacy auxiliary plotting example.
# The original script loaded an experiment-specific file at import time.
# It is disabled pending review of the ADC calibration and source-data metadata.
if __name__ == "__main__":
    raise SystemExit("Unvalidated example: do not infer volts from raw ADC without calibrated metadata.")

# Historical original script retained below as comments for traceability.
# import numpy as np
# from picosdk.ps5000a import ps5000a as ps
# # Charger le fichier
# data = np.load("captured_signals_20251118_173459.npy")
#
# print("Forme des données :", data.shape)  # Affiche la forme (nombre de captures, nombre d'échantillons)
# print("Type des données :", data.dtype)   # Affiche le type des données (généralement int16 pour le PicoScope)
#
# # Première capture
# first_capture = data[0, :]
# print("Première capture :", first_capture[:10])  # Affiche les 10 premiers échantillons
#
# # Échantillon 50 de la première capture
# sample_50 = data[0, 50]
# print("Échantillon 50 :", sample_50)
#
#
# def adc_to_mv(adc_counts, voltage_range_mv, resolution):
#     max_adc = {
#         ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]: 127,
#         ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]: 2047,
#         ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_14BIT"]: 8191,
#         ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_15BIT"]: 16383,
#         ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]: 32767
#     }.get(resolution)
#     return (adc_counts / max_adc) * voltage_range_mv
#
# # Exemple : convertir la première capture en mV
# voltage_range_mv = 5000  # Exemple : plage de 5V
# resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
# first_capture_mv = adc_to_mv(first_capture, voltage_range_mv, resolution)
# print("Première capture en mV :", first_capture_mv[:10])
#
#
# import matplotlib.pyplot as plt
#
# # Tracer la première capture
# plt.plot(first_capture_mv)
# plt.xlabel("Échantillon")
# plt.ylabel("Tension (mV)")
# plt.title("Signal capturé (première acquisition)")
# plt.grid()
# plt.show()
#
#
#
#
