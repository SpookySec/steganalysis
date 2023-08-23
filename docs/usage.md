# Usage

In the context of this guide, let's assume that the project root directory is where you have installed/cloned this tool.

## Preparing the Environment

Before you start, ensure that you have installed all the necessary dependencies (Python version, additional packages, etc.), mentioned in the [`installation.md`](installation.md).

## Running the Tool

The tool can be accessed from the command line. Here we'll guide you on how to use it.

1. Navigate to the project root directory.

2. Run the main script with the file you want to analyze:

```sh
python script.py -f path_to_your_file
```
(Replace `path_to_your_file` with the path to the file that you want to analyze).

## Understanding the Output
Once you've run the command, the tool will start the analysis and will print the output to the command line. The output will include the analysis results obtained from each of the integrated utilities (_stegsolve, _steghide, _zsteg, _foremost, _binwalk).

If the tool is able to uncover any hidden information within the file, it will display that information in the output, and write
the results to the output directory as stated by the tool.

Also, make sure the tool has necessary permissions to read the file and write the output.