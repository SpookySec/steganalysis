# Main Function

All these functions run the corresponding tool on a provided file and handle the output in different ways depending on the specific tool and function. They provide a series of different methods for scanning and analyzing files for hidden data — an important process in digital forensic investigations and cybersecurity assessments.

This is the main function that takes an input PDF file. It extracts images, performs steganalysis, finds all images in the current directory, processes each one, fetches all WAV files, runs `stegwav` for each, followed by white space steganography detection. Additionally, it plots entropy changes, delays for 2 seconds, then prints the directory tree.
