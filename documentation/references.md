https://blog.trailofbits.com/2024/06/11/exploiting-ml-models-with-pickle-file-attacks-part-1/
https://blog.trailofbits.com/2024/06/11/exploiting-ml-models-with-pickle-file-attacks-part-2/
https://hiddenlayer.com/research/weaponizing-machine-learning-models-with-ransomware/
https://huggingface.co/docs/hub/security-pickle
https://hiddenlayer.com/research/pickle-strike/
https://v1.marksolters.com/programming/2015/05/09/intel-hex-viewer.html

Python offers several ways to scan binary files depending on your specific needs:

1. Reading Raw Bytes:
* open() function: The most basic way is to open the file in binary mode ('rb') and read the bytes directly.

```python
with open('binary_file.bin', 'rb') as f:
    data = f.read()

# Process the binary data as needed
```

* struct module: Use this module to unpack structured binary data based on a specific format string.  

```python
import struct

with open('binary_file.bin', 'rb') as f:
    value = struct.unpack('i', f.read(4))[0]  # Unpack a 4-byte integer
```

2. Libraries for Specific Formats:

* `pickle` module: For reading and writing Python objects in a binary format.
* `image` libraries (e.g., PIL, OpenCV): For working with image files like JPEG or PNG.
* `audio` libraries (e.g., librosa, soundfile): For working with audio files like WAV or MP3.

3. Tools for Security Analysis:

* `YARA:` A powerful pattern-matching tool for identifying and classifying malware samples. It has a Python API for integration into your scripts.
* `ClamAV:` An open-source antivirus engine that can be used to scan files for malware signatures.
* `binwalk:` A tool for analyzing, extracting, and visualizing firmware images.

4. Building Custom Scanners:

* `Regular expressions:` Use regular expressions to search for specific patterns within the binary data.
* `Heuristic analysis:` Analyze the structure and characteristics of the binary file to identify potential threats.
* `Disassembly:` Use a disassembler like `Capstone` to examine the assembly code of the binary

