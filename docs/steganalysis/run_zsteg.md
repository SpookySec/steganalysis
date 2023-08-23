# `run_zsteg` Function

Zsteg is a tool designed to detect LSB steganography in PNG and BMP files, an often employed method to hide secret data in the least significant bits of pixel values.

The function checks if `zsteg` is in the PATH. If it doesn't, logs an error and suggests installation command. If `zsteg` exists, runs `zsteg` on the provided image path and stores the output.
