# `run_steghide` Function

This tool makes use of the steghide command, a steganography tool which hides, in an undetectable manner, data within various types of files. In particular, it embeds data within the least significant bits of images and audio files without causing noticeable changes or distortions.

This function checks for `steghide` in the PATH. If not found, it logs an error message and ends. If exists, runs `steghide` on the provided image path to extract hidden information. The result is stored.
