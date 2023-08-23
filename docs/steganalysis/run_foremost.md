# `run_foremost` Function

It uses the foremost tool. Foremost is a forensic data recovery program, useful for extracting files based on their headers, footers, and internal data structures. This process is known as 'file carving'. It was developed by the members of the United States Air Force Office of Special Investigations.

This function located `foremost` in the PATH. If it doesn't exist it logs an error message and recommends the installation command. If `foremost` exists, it runs `foremost` on the given file path, storing the output in a specified directory.
