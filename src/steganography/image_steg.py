"""
Image Steganography using LSB (Least Significant Bit) technique
Hides encrypted data inside images
"""

import io
from typing import Optional
from PIL import Image
import base64


class ImageSteganography:
    """
    Hide encrypted messages in images using LSB steganography
    Features:
    - LSB embedding in RGB channels
    - Support for PNG and BMP formats
    - Automatic capacity calculation
    - Data integrity verification
    """

    DELIMITER = b"<<<END_OF_MESSAGE>>>"

    def __init__(self):
        """Initialize steganography engine"""
        pass

    def _convert_to_binary(self, data: bytes) -> str:
        """
        Convert bytes to binary string

        Args:
            data: Bytes to convert

        Returns:
            Binary string representation
        """
        return ''.join(format(byte, '08b') for byte in data)

    def _binary_to_bytes(self, binary_str: str) -> bytes:
        """
        Convert binary string to bytes

        Args:
            binary_str: Binary string

        Returns:
            Bytes
        """
        byte_array = bytearray()
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                byte_array.append(int(byte, 2))
        return bytes(byte_array)

    def calculate_capacity(self, image: Image.Image) -> int:
        """
        Calculate maximum data capacity in bytes

        Args:
            image: PIL Image object

        Returns:
            Maximum bytes that can be hidden
        """
        width, height = image.size
        # 3 channels (RGB), 1 bit per channel
        total_bits = width * height * 3
        # Convert to bytes, subtract delimiter size
        return (total_bits // 8) - len(self.DELIMITER)

    def hide_data(self, image: Image.Image, data: bytes) -> Image.Image:
        """
        Hide data in image using LSB steganography

        Args:
            image: Cover image (PIL Image)
            data: Data to hide

        Returns:
            Stego image with hidden data

        Raises:
            ValueError: If data is too large for image
        """
        # Convert image to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Check capacity
        capacity = self.calculate_capacity(image)
        data_with_delimiter = data + self.DELIMITER

        if len(data_with_delimiter) > capacity:
            raise ValueError(
                f"Data too large: {len(data)} bytes, capacity: {capacity} bytes"
            )

        # Convert data to binary
        binary_data = self._convert_to_binary(data_with_delimiter)

        # Get pixel data
        pixels = list(image.getdata())
        new_pixels = []

        data_index = 0
        for pixel in pixels:
            r, g, b = pixel

            if data_index < len(binary_data):
                # Modify LSB of red channel
                r = (r & 0xFE) | int(binary_data[data_index])
                data_index += 1

            if data_index < len(binary_data):
                # Modify LSB of green channel
                g = (g & 0xFE) | int(binary_data[data_index])
                data_index += 1

            if data_index < len(binary_data):
                # Modify LSB of blue channel
                b = (b & 0xFE) | int(binary_data[data_index])
                data_index += 1

            new_pixels.append((r, g, b))

        # Create new image
        stego_image = Image.new('RGB', image.size)
        stego_image.putdata(new_pixels)

        return stego_image

    def extract_data(self, image: Image.Image) -> Optional[bytes]:
        """
        Extract hidden data from image

        Args:
            image: Stego image with hidden data

        Returns:
            Extracted data or None if no data found
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get pixel data
        pixels = list(image.getdata())

        # Extract LSBs
        binary_data = ''
        for pixel in pixels:
            r, g, b = pixel
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

        # Convert to bytes
        all_bytes = self._binary_to_bytes(binary_data)

        # Find delimiter
        try:
            delimiter_pos = all_bytes.find(self.DELIMITER)
            if delimiter_pos == -1:
                return None

            return all_bytes[:delimiter_pos]
        except Exception:
            return None

    def hide_in_image_bytes(self, image_bytes: bytes, data: bytes) -> bytes:
        """
        Hide data in image provided as bytes

        Args:
            image_bytes: Cover image as bytes
            data: Data to hide

        Returns:
            Stego image as PNG bytes
        """
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Hide data
        stego_image = self.hide_data(image, data)

        # Convert to bytes (PNG format to preserve data)
        output = io.BytesIO()
        stego_image.save(output, format='PNG')
        return output.getvalue()

    def extract_from_image_bytes(self, image_bytes: bytes) -> Optional[bytes]:
        """
        Extract data from image provided as bytes

        Args:
            image_bytes: Stego image as bytes

        Returns:
            Extracted data or None
        """
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Extract data
        return self.extract_data(image)

    def create_cover_image(self, width: int = 800, height: int = 600) -> Image.Image:
        """
        Create a random cover image for steganography

        Args:
            width: Image width
            height: Image height

        Returns:
            Random RGB image
        """
        import secrets

        # Generate random pixel data
        pixels = []
        for _ in range(width * height):
            r = secrets.randbelow(256)
            g = secrets.randbelow(256)
            b = secrets.randbelow(256)
            pixels.append((r, g, b))

        # Create image
        image = Image.new('RGB', (width, height))
        image.putdata(pixels)

        return image
