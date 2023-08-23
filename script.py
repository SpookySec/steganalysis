import subprocess
import pkg_resources
import sys
import os

# Function to install missing python libraries
def install_missing_libraries(requiredLibraries):
    print("Installing missing packages...", end="")
    
    # Retrieve a set of installed packages
    installedPackages = {pkg.key for pkg in pkg_resources.working_set}
    
    # Find the difference between required libraries and installed packages
    missingLibraries = requiredLibraries - installedPackages

    # If there are any missing libraries
    if missingLibraries:
        # Get the system python executable path
        python = sys.executable
        total = len(missingLibraries)
        
        # Iterate over each missing library
        for i, library in enumerate(missingLibraries, 1):
            # Use subprocess to call pip install command for the missing library
            subprocess.check_call(
                [python, "-m", "pip", "install", "--upgrade", library], stdout=subprocess.DEVNULL
            )
            # Calculate the progress percentage
            progress = (i / total) * 100
            
            # Print the progress on the same line and flush the output to the terminal
            sys.stdout.write("\rInstalling missing packages...%d%%" % progress)
            sys.stdout.flush()
            
     # Print complete message if there aren't any missing packages
    else:
        print("No missing packages to install.")

# Function to install system packages
def install_system_package(package_name):
    print(f"Installing {package_name}...")
    os.system(f'sudo apt install -y {package_name}')

requiredLibraries = {
    "pymupdf",
    "python-magic",
    "argparse",
    "numpy",
    "pillow",
    "colorama",
    "datetime",
    "plotext",
    "pdfplumber",
}

install_missing_libraries(requiredLibraries)
install_system_package('libsndfile1-dev') # Required for stegwav

import fitz
import re
import binascii
import magic
import subprocess
import base64
import argparse
import shutil
import sys
import math
import numpy as np
import hashlib
import pdfplumber
from PIL import Image
from colorama import Fore
from datetime import datetime
import plotext as plt
from time import sleep

output_name = f'extracted_{datetime.now().strftime("%h-%F-%S")}'
author = "[CHANGE ME]"

print("=" * 20)
print(f"Written by: {author}")
print(f"Saving output to: {output_name}/")
print("=" * 20)
print("\n" * 2)

# Function to display current directory as a tree, similar to `tree` command
def print_tree(directory, delay=0, indent='', base=''):
    if not os.path.exists(directory):
        CustomLogger.error(f"Directory '{directory}' doesn't exist.")
        return

    items = os.listdir(directory)
    dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
    files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
    
    for i, directory in enumerate(dirs):
        if i == len(dirs) - 1 and not files:
            print(f'{indent}└── {directory}')
            next_indent = f'{indent}    '
        else:
            print(f'{indent}├── {directory}')
            next_indent = f'{indent}│   '
        sleep(delay)  # delay processing 
        sub_dir = os.path.join(base, directory)
        if os.path.exists(sub_dir):
            print_tree(sub_dir, delay, base=sub_dir, indent=next_indent)

    for i, file in enumerate(files):
        if i == len(files) - 1:
            print(f'{indent}└── {file}')
        else:
            print(f'{indent}├── {file}')
        sleep(delay)  # delay processing 


# Regular expression for finding two continous whitespaces (White space steg detection)
def detect_white_space_steg(text):
    pattern = r"[a-zA-Z0-9][ ]{2,}[a-zA-Z0-9]"
    return re.findall(pattern, text)


# Function for sorting through all unique images in a given directory
def find_unique_images(directory):
    hash_keys = dict()
    image_list = []

    image_file_types = [".jpg", ".png", ".jpeg", ".gif"]

    for dirpath, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in image_file_types:
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "rb") as f:
                    img_hash = hashlib.md5(f.read()).hexdigest()
                    if img_hash not in hash_keys:
                        hash_keys[img_hash] = filepath
                        image_list.append(filepath)
    return image_list


# Function for sorting through all unique images in a given directory
def find_unique_wav_files(directory):
    hash_keys = dict()
    wav_files = []

    for dirpath, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() == ".wav":
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    if file_hash not in hash_keys: # file is unique
                        hash_keys[file_hash] = filepath
                        wav_files.append(filepath)

    return wav_files

def process_image(image_path):
    base, ext = os.path.splitext(image_path)

    convert_path = shutil.which("convert")

    if convert_path == None:
        CustomLogger.error("'convert' was not found in PATH!\n")
        CustomLogger.info("Consider running: 'sudo apt install imagemagick'")
        return

    # Extract color planes and negative
    for color in ["R", "G", "B"]:
        subprocess.check_call(
            [
                "convert",
                image_path,
                "-channel",
                color,
                "-separate",
                f"{base}_{color.lower()}{ext}",
            ]
        )
        subprocess.check_call(
            [
                "convert",
                f"{base}_{color.lower()}{ext}",
                "-negate",
                f"{base}_{color.lower()}_negate{ext}",
            ]
        )

        for bit_plane in range(8):  # bit planes 0-7
            extract_bit_plane(image_path, color.lower(), bit_plane)
            gray_bits(image_path, bit_plane)

    # Create grayscale image
    subprocess.check_call(
        ["convert", image_path, "-colorspace", "Gray", f"{base}_grayscale{ext}"]
    )

    # Negate all colors
    subprocess.check_call(["convert", image_path, "-negate", f"{base}_negate{ext}"])


def gray_bits(image_path, bit_plane):
    image = Image.open(image_path)
    image_array = np.array(image)

    bit_plane_image = np.right_shift(image_array, bit_plane) & 1
    bit_plane_image = bit_plane_image * 255  # scaling to gray scale
    gray_bit_image = Image.fromarray(np.uint8(bit_plane_image))

    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_gray_bit{bit_plane}.png"

    gray_bit_image.save(output_path)
    CustomLogger.success(f"Gray Bits Image saved as {output_path}")


def extract_bit_plane(image_path, color_channel, bit_plane):
    image = Image.open(image_path)
    pixels = image.load() 
    width, height = image.size

    for y in range(height):
        for x in range(width):
            pixel_data = pixels[x, y]

            if len(pixel_data) == 4:
                r, g, b, a = pixel_data
            else:
                r, g, b = pixel_data

            if color_channel.lower() == "r":
                r = (r >> bit_plane) & 1
                g = b = 0
            elif color_channel.lower() == "g":
                g = (g >> bit_plane) & 1
                r = b = 0
            elif color_channel.lower() == "b":
                b = (b >> bit_plane) & 1
                r = g = 0

            pixels[x, y] = (r * 255, g * 255, b * 255)

    base, ext = os.path.splitext(image_path)
    output_path = f"{base}_{color_channel}{bit_plane}.png"
    image.save(output_path)

    CustomLogger.success(f"Bit Plane Image saved as {output_path}")

# def process_image(image_path):
    # base, ext = os.path.splitext(image_path)

    # convert_path = shutil.which("convert")

    # if convert_path == None:
        # CustomLogger.error("'convert' was not found in PATH!\n")
        # CustomLogger.info("Consider running: 'sudo apt install imagemagick'")
        # return


    # # Extract color planes and negative
    # for color in ["R", "G", "B"]:
        # subprocess.check_call(
            # [
                # "convert",
                # image_path,
                # "-channel",
                # color,
                # "-separate",
                # f"{base}_{color.lower()}{ext}",
            # ]
        # )
        # subprocess.check_call(
            # [
                # "convert",
                # f"{base}_{color.lower()}{ext}",
                # "-negate",
                # f"{base}_{color.lower()}_negate{ext}",
            # ]
        # )

    # # Create grayscale image
    # subprocess.check_call(
        # ["convert", image_path, "-colorspace", "Gray", f"{base}_grayscale{ext}"]
    # )

    # # Negate all colors
    # subprocess.check_call(["convert", image_path, "-negate", f"{base}_negate{ext}"])


def calculate_entropy(data):
    # Calculate the probability distribution of each byte value
    value, counts = np.unique(np.frombuffer(data, dtype=np.uint8), return_counts=True)
    prob = counts / len(data)

    # Calculate entropy using the formula: H(X) = -sum(p(x) * log2(p(x)))
    entropy = -np.sum(prob * np.log2(prob))

    return entropy


def plot_entropy_changes(file_path):
    chunk_size = 1024  # Adjust the chunk size based on your file size
    entropies = []

    with open(file_path, "rb") as file:
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            entropy = calculate_entropy(data)
            entropies.append(entropy)

    plt.plot(entropies, marker="braille")
    plt.canvas_color("gray")
    plt.axes_color("black")
    plt.ticks_color("white")
    plt.xlabel("Chunk Index")
    plt.ylabel("Entropy")
    plt.title(f"Entropy Change of {file_path}")
    plt.grid()

    plt.show()


class CustomLogger:
    def success(msg):
        timestamp = datetime.now().strftime("%T")
        print(
            f"{Fore.CYAN}{timestamp} {Fore.GREEN}SUCCESS{Fore.RESET} | {Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Fore.RESET} {msg}"
        )

    def error(msg):
        timestamp = datetime.now().strftime("%T")
        print(
            f"{Fore.CYAN}{timestamp} {Fore.RED}ERROR{Fore.RESET}   |{Fore.RESET} {Fore.WHITE}[{Fore.RED}-{Fore.WHITE}]{Fore.RESET} {msg}"
        )

    def warning(msg):
        timestamp = datetime.now().strftime("%T")
        print(
            f"{Fore.CYAN}{timestamp} {Fore.YELLOW}WARNING{Fore.RESET} |{Fore.RESET} {Fore.WHITE}[{Fore.YELLOW}!{Fore.WHITE}]{Fore.RESET} {msg}"
        )

    def info(msg):
        timestamp = datetime.now().strftime("%T")
        print(
            f"{Fore.CYAN}{timestamp} {Fore.BLUE}INFO{Fore.RESET}    |{Fore.RESET} {Fore.WHITE}[{Fore.BLUE}*{Fore.WHITE}]{Fore.RESET} {msg}"
        )


class PDF:
    def __init__(self, filepath) -> None:
        self.filepath = filepath
        self.filetype = magic.from_file(self.filepath, mime=True)

    def is_pdf(self) -> bool:
        return self.filetype == "application/pdf"

    def extract_text(self):
        text = ""

        try:
            with pdfplumber.open(self.filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
            return text
        except:
            return
            

    def extract_images(
        self, extractedpath=os.path.join(os.getcwd(), output_name)
    ) -> list[int]:
        if not os.path.exists(extractedpath):
            os.mkdir(extractedpath)

        if not self.is_pdf():
            CustomLogger.warning(
                f"'{self.filepath}' does not seem like a valid PDF file."
            )
            return

        doc = fitz.open(self.filepath, filetype="pdf")
        extracted_images = []
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                base = doc.extract_image(xref)
                image_data = base["image"]
                image_path = os.path.join(extractedpath, f"p{i}-{xref}.png")
                with open(image_path, "wb") as f:
                    f.write(image_data)
                extracted_images.append(image_path)

        # print(f'Extracted files: {extracted_images}')  # Add debug statement
        return extracted_images

    def extract_binaries(self, extractedpath=os.path.join(os.getcwd(), output_name)):
        if not os.path.exists(extractedpath):
            os.mkdir(extractedpath)

        with open(self.filepath, "rb") as file:
            content = file.read().decode(errors="replace")

        hex_strings = re.findall(r"endobj[\s]*(<[0-9a-fA-F]*>)[\s]*endobj", content)

        extracted_files = []
        for i, hex_string in enumerate(hex_strings):
            hex_string = hex_string[1:-1]  # Remove the < and > at the ends
            binary_data = binascii.unhexlify(hex_string)

            # Write the binary data to a file
            output_path = os.path.join(extractedpath, f"data{i}.bin")

            with open(output_path, "wb") as output_file:
                output_file.write(binary_data)

            extracted_files.append(output_path)

        # print(f'Extracted hex files: {extracted_files}')  # Add debug statement
        return extracted_files


class SteganalysisTool:
    def __init__(self, pdf):
        self.pdf = pdf

    def decode_and_save_image(
        self,
        base64_data,
        filename,
        extractedpath=os.path.join(os.getcwd(), output_name),
    ):
        if not os.path.exists(extractedpath):
            os.mkdir(extractedpath)

        # Check if padding is required
        missing_padding = len(base64_data) % 4
        if missing_padding != 0:
            base64_data += "=" * (4 - missing_padding)

        image_data = base64.b64decode(base64_data)
        image_path = os.path.join(extractedpath, filename)

        with open(image_path, "wb") as f:
            f.write(image_data)
        return image_path

    def perform_steganalysis(self, extracted_files):
        self._run_binwalk(self.pdf.filepath)
        self._run_foremost(self.pdf.filepath)
        self._run_strings(self.pdf.filepath)

        for file_path in extracted_files:
            file_type = magic.from_file(file_path, mime=True)
            # Add debug statement
            CustomLogger.info(f"Performing steganalysis on {file_path}")
            if file_type == "image/jpeg":
                self._run_stegsolve(file_path)
                self._run_steghide(file_path)
            elif file_type == "image/png":
                self._run_zsteg(file_path)

    def _run_strings(self, file_path):
        strings_path = shutil.which("strings")

        if strings_path == None:
            CustomLogger.error("'strings' was not found in PATH!\n")
            CustomLogger.info("Consider running: 'sudo apt install binutils'")
            return

        output_path = f"{output_name}/strings.txt"  # Set the output file path

        CustomLogger.info(f"Running strings on {file_path}")
        result = subprocess.run(
            [strings_path, file_path], stdout=subprocess.PIPE, text=True
        )

        try:
            with open(output_path, "w+") as file:
                file.write(result.stdout)
            CustomLogger.success(f"Strings output written to {output_path}")
        except Exception as e:
            CustomLogger.warning(f"Error writing to {output_path}: {e}")

    def _run_stegsolve(self, image_path):
        stegsolve_path = shutil.which("stegsolve")

        if stegsolve_path == None:
            CustomLogger.error("stegsolve.jar was not found in PATH!\n")
            return

        CustomLogger.info(f"Running Stegsolve on {image_path}...")
        result = subprocess.run(
            ["java", "-jar", stegsolve_path, image_path],
            stdout=subprocess.PIPE,
            text=True,
        )
        CustomLogger.success(result.stdout)

    def _run_steghide(self, image_path):
        steghide_path = shutil.which("steghide")

        if steghide_path == None:
            CustomLogger.error("steghide was not found in PATH!\n")
            CustomLogger.info("Consider running: 'sudo apt install steghide'")
            return

        CustomLogger.info(f"Running steghide on {image_path}...")
        result = subprocess.run(
            [steghide_path, "extract", "-sf", image_path],
            stdout=subprocess.PIPE,
            text=True,
        )
        CustomLogger.success(result.stdout)

    def _run_zsteg(self, image_path):
        zsteg_path = shutil.which("zsteg")

        if zsteg_path == None:
            CustomLogger.error("zsteg was not found in PATH!\n")
            CustomLogger.info("Consider running: 'sudo gem install zsteg'")
            return

        CustomLogger.info(f"Running zsteg on {image_path}")
        result = subprocess.run(
            [zsteg_path, image_path], stdout=subprocess.PIPE, text=True
        )
        CustomLogger.success(result.stdout)

    def _run_foremost(self, file_path):
        foremost_path = shutil.which("foremost")

        if foremost_path == None:
            CustomLogger.error("foremost was not found in PATH!\n")
            CustomLogger.info("Consider running: 'sudo apt install foremost'")
            return

        CustomLogger.info(f"Running foremost on {file_path}")
        result = subprocess.run(
            [foremost_path, "-i", file_path, "-o", f"{output_name}/foremost/"],
            stdout=subprocess.PIPE,
            text=True,
        )
        # CustomLogger.success(result.stdout)

        try:
            with open(f"{output_name}/foremost/audit.txt") as audit:
                print(audit.read())
        except FileNotFoundError:
            CustomLogger.warning(f"Audit file not found!")

    def _run_binwalk(self, file_path):
        binwalk_path = shutil.which("binwalk")

        if binwalk_path == None:
            CustomLogger.error("binwalk was not found in PATH!\n")
            CustomLogger.info("Consider running: 'sudo apt install binwalk'")
            return

        CustomLogger.info(f"Running binwalk on {file_path}")
        result = subprocess.run(
            [binwalk_path, "-e", "-C", f"{output_name}/binwalk/", file_path],
            stdout=subprocess.PIPE,
            text=True,
        )
        CustomLogger.success(result.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="Automated steg analysis on PDF files."
    )

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)

    parser.add_argument("--file", "-f", help="Path to pdf file", required=True)
    args = parser.parse_args()

    pdf = PDF(args.file)

    if not pdf.is_pdf():
        CustomLogger.error(f"'{pdf.filepath}' does not seem like a valid PDF file.")
        return

    tool = SteganalysisTool(pdf)

    extracted_images = tool.pdf.extract_images()
    tool.perform_steganalysis(extracted_images)

    # Find all images in current dir
    all_images = find_unique_images(f"{os.getcwd()}/{output_name}")
    [process_image(img) for img in all_images]
    tool.perform_steganalysis(all_images)

    # Find all wav files
    all_wavs = find_unique_wav_files(f"{os.getcwd()}/{output_name}")
    [run_stegwav(wav) for wav in all_wavs]

    text = tool.pdf.extract_text()
    
    if detect_white_space_steg(text):
        CustomLogger.success('Whitespace steganography detected!')
    else:
        CustomLogger.warning('No whitespace steganography detected.')

    plot_entropy_changes(args.file)

    sleep(2)

    os.chdir(output_name)
    print_tree('.', delay=0.1)


if __name__ == "__main__":
    main()
