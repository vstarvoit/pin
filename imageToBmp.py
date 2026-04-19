from PIL import Image
import os

def convert_to_bmp(input_path, output_path=None):
    try:
        img = Image.open(input_path)

        if output_path is None:
            base = os.path.splitext(input_path)[0]
            output_path = base + ".bmp"

        img.convert("RGBA").save(output_path, "BMP")

        print(f"Converted '{input_path}' to '{output_path}' successfully.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    convert_to_bmp("1.webp")