## Stegastatter, an Open-Source Small-Scale Steganography Engine
Stegastatter is a steganography engine that uses LSB (Least Significant Bit) and BPCS (Bit Plane Complexity Segmentation) to hide, extract, and estimate the capacity of images. Additionally stegastatter includes two steganalysis algorithms that can calculate the diffrences between two images and slice it into 24 seperate bit planes.
Apart from steganography/steganalysis, Stegastatter uses a wrapping mechanism that consists of encryption, byte shuffling, and error correction.
A theoretical overview for the concepts in this project can be found [here](https://github.com/Jebbex1/Stegastatter/blob/main/Stegastatter%20Theoretical%20Overview.docx).

## Usage Notes
This module is unsafe in reguard to errror handling. If the functions of this module are called with improper parameters / with invalid data (e.g. attempting to extract data from an image with no data hidden in it), errors will be raised.
Consult the errors.py file for info on different errors.