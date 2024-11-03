import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import os
import sys
import logging
import subprocess
from PIL import Image, ImageTk
import numpy as np  # Import NumPy

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('VideoGenerator')
# Suppress DEBUG logs from PIL
logging.getLogger('PIL').setLevel(logging.WARNING)

class VideoTextGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Text Generator")
        
        # Determine the script directory
        if getattr(sys, 'frozen', False):
            script_dir = Path(sys._MEIPASS)
        else:
            script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # Paths to video folders
        self.lower_case_path = script_dir / "Source" / "LOWER_CASE"
        self.upper_case_path = script_dir / "Source" / "UPPER_CASE"
        
        # Path to preview images
        self.preview_images_path = script_dir / "PreviewImages"
        
        # Video parameters
        self.VIDEO_DURATION = 10  # Duration in seconds
        self.VIDEO_WIDTH = 1920   # Width in pixels
        self.VIDEO_HEIGHT = 1080  # Height in pixels
        self.FPS = "25"           # Frames per second
        
        # Character width ratios for better spacing
        self.char_width_ratios = {
            'm': 1.2,  # m is wider
            'w': 1.2,  # w is wider
            'default': 1.0  # default ratio for all other characters
        }
        
        # Initialize parameters with default values
        self.base_char_size = 150  # default character size
        self.char_spacing_factor = -0.7  # default character spacing factor
        self.space_width = 20  # default space width
        
        # Load preview images
        self.preview_images = self.load_preview_images()
        
        # Set up the GUI
        self.setup_gui()
    
    def load_preview_images(self):
        """
        Loads all preview images into a dictionary for quick access.
        """
        images = {}
        for image_file in self.preview_images_path.glob("*.png"):
            key = image_file.stem  # e.g., 'lower_a' or 'upper_A'
            image = Image.open(image_file).convert('RGBA')  # Ensure RGBA mode
            images[key] = image
        return images

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Text input field
        ttk.Label(main_frame, text="Enter text:").grid(row=0, column=0, sticky=tk.W)
        self.text_input = ttk.Entry(main_frame, width=40)
        self.text_input.insert(0, "Ouais Ouais")  # Default text
        self.text_input.grid(row=0, column=1, padx=5, pady=5, columnspan=3)
        self.text_input.bind("<KeyRelease>", self.update_preview)
        
        # Radio buttons for case selection
        self.case_var = tk.StringVar(value="mixed")
        ttk.Radiobutton(main_frame, text="Uppercase", variable=self.case_var, 
                       value="upper", command=self.update_preview).grid(row=1, column=0)
        ttk.Radiobutton(main_frame, text="Lowercase", variable=self.case_var, 
                       value="lower", command=self.update_preview).grid(row=1, column=1)
        ttk.Radiobutton(main_frame, text="Mixed case", variable=self.case_var, 
                       value="mixed", command=self.update_preview).grid(row=1, column=2)
        
        # Spacing controls
        ttk.Label(main_frame, text="Character Size:").grid(row=2, column=0, sticky=tk.W)
        self.char_size_var = tk.IntVar(value=self.base_char_size)
        char_size_spin = ttk.Spinbox(main_frame, from_=50, to=300, increment=10, textvariable=self.char_size_var, command=self.update_preview)
        char_size_spin.grid(row=2, column=1, sticky=tk.W)

        ttk.Label(main_frame, text="Char Spacing:").grid(row=3, column=0, sticky=tk.W)
        self.char_spacing_var = tk.DoubleVar(value=self.char_spacing_factor)
        char_spacing_spin = ttk.Spinbox(main_frame, from_=-1.0, to=0.0, increment=0.1, textvariable=self.char_spacing_var, format="%.1f", command=self.update_preview)
        char_spacing_spin.grid(row=3, column=1, sticky=tk.W)
        
        # Button to generate video
        ttk.Button(main_frame, text="Generate Video", 
                  command=self.generate_video).grid(row=4, column=1, pady=10)
        
        # Canvas for preview with 16:9 aspect ratio
        self.preview_canvas = tk.Canvas(main_frame, width=800, height=450, bg="black")
        self.preview_canvas.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Update preview initially
        self.update_preview()

    def screen_blend(self, img1, img2):
        """
        Blends two images using the 'screen' blend mode.
        """
        arr1 = np.array(img1).astype('float') / 255.0
        arr2 = np.array(img2).astype('float') / 255.0

        # Separate the RGB and alpha channels
        rgb1 = arr1[..., :3]
        alpha1 = arr1[..., 3]
        rgb2 = arr2[..., :3]
        alpha2 = arr2[..., 3]

        # Compute the screen blending for RGB channels
        rgb = 1 - (1 - rgb1) * (1 - rgb2)

        # Compute the combined alpha channel
        alpha = alpha1 + alpha2 * (1 - alpha1)

        # Handle invalid values
        alpha = np.clip(alpha, 0, 1)
        rgb = np.clip(rgb, 0, 1)

        # Multiply RGB by alpha
        rgb = rgb * alpha[..., np.newaxis]

        # Combine RGB and alpha channels
        result = np.dstack((rgb, alpha))

        # Convert back to uint8
        result = (result * 255).astype('uint8')

        # Create an image from the result
        return Image.fromarray(result, 'RGBA')

    def update_preview(self, *args):
        """
        Updates the preview canvas to show the current text placement with the blending effect.
        """
        # Clear the canvas
        self.preview_canvas.delete("all")
        
        # Get the text
        text = self.text_input.get().strip()
        if not text:
            return

        # Apply chosen case
        case_choice = self.case_var.get()
        if case_choice == "upper":
            text_display = text.upper()
        elif case_choice == "lower":
            text_display = text.lower()
        else:
            text_display = text

        # Get the parameters from the GUI variables
        self.base_char_size = self.char_size_var.get()
        self.char_spacing_factor = self.char_spacing_var.get()

        # Base character size and spacing
        base_char_size = self.base_char_size
        char_spacing = int(base_char_size * self.char_spacing_factor)

        # Collect valid characters and their images
        char_images = []
        for char in text_display:
            if char.isalpha():
                case = "upper" if char.isupper() else "lower"
                key = f"{case}_{char.lower()}"
                image = self.preview_images.get(key)
                if image:
                    char_images.append(image)
                else:
                    logger.warning(f"No preview image for character '{char}'")
            elif char.isspace():
                # Add a None to represent space
                char_images.append(None)
            else:
                logger.warning(f"Unsupported character '{char}' in text")

        if not char_images:
            return

        # Create base image for blending
        preview_width = int(self.preview_canvas['width'])
        preview_height = int(self.preview_canvas['height'])
        base_image = Image.new('RGBA', (preview_width, preview_height), (0, 0, 0, 255))

        # Calculate positions
        total_width = 0
        char_positions = []
        for img in char_images:
            if img is None:
                total_width += self.space_width  # Add width for space
                char_positions.append(None)
            else:
                total_width += base_char_size + char_spacing
                char_positions.append(total_width - base_char_size - char_spacing)

        total_width -= char_spacing  # Remove extra spacing
        x_offset = (preview_width - total_width) // 2
        y_offset = (preview_height - base_char_size) // 2

        # Blend images using screen blending
        current_image = base_image.copy()
        for pos, img in zip(char_positions, char_images):
            if img is not None and pos is not None:
                resized_img = img.resize((base_char_size, base_char_size), Image.LANCZOS).convert('RGBA')
                x = x_offset + pos
                y = y_offset
                temp_image = Image.new('RGBA', current_image.size, (0, 0, 0, 0))
                temp_image.paste(resized_img, (int(x), int(y)), mask=resized_img)
                # Perform screen blending
                current_image = self.screen_blend(current_image, temp_image)
            elif pos is None:  # Space character
                x_offset += self.space_width

        # Convert to Tkinter image
        tk_image = ImageTk.PhotoImage(current_image.convert('RGB'))
        self.preview_canvas.image = tk_image  # Keep reference
        self.preview_canvas.create_image(0, 0, anchor='nw', image=tk_image)

    def get_video_path(self, char, case="lower"):
        """
        Returns the full path to the video file corresponding to the character and specified case.
        """
        base_path = self.lower_case_path if case == "lower" else self.upper_case_path
        video_file = f"{char.lower()}.mp4"
        full_path = base_path / video_file
        logger.debug(f"Looking for video file: {full_path} (exists: {full_path.exists()})")
        return full_path

    def generate_video(self):
        """
        Generates the video using FFmpeg by combining character videos with improved spacing
        """
        text = self.text_input.get().strip()
        if not text:
            text = "Ouais Ouais"

        # Apply chosen case
        case_choice = self.case_var.get()
        if case_choice == "upper":
            text = text.upper()
        elif case_choice == "lower":
            text = text.lower()

        logger.info(f"Generating video for text: '{text}' with case: {case_choice}")

        try:
            # Collect valid videos for each character
            valid_chars = []
            for i, char in enumerate(text):
                if char.isalpha() or char.isdigit() or char.isspace():
                    case = "upper" if char.isupper() else "lower"
                    if char.isspace():
                        valid_chars.append((i, None))
                    else:
                        video_path = self.get_video_path(char.lower(), case)
                        if video_path.exists():
                            valid_chars.append((i, str(video_path)))
                        else:
                            raise FileNotFoundError(f"No video found for character '{char}'")
                else:
                    raise ValueError(f"Unsupported character '{char}' in text")

            if not valid_chars:
                raise ValueError("No valid characters to process")

            # Base character size calculation
            base_char_size = 300
            char_spacing = int(base_char_size * -0.7)  # Increased overlap for closer letters
            space_width = 50  # Fixed space width

            # Calculate total width considering individual character widths
            total_width = 0
            char_positions = []
            current_x = 0

            for i, (char_index, path) in enumerate(valid_chars):
                if path is None:  # Space character
                    current_x += self.space_width
                    char_positions.append(None)
                else:
                    if i > 0:
                        current_x += char_spacing
                    char_width = base_char_size
                    char_positions.append((current_x, char_width))
                    current_x += char_width

            total_width = current_x

            # Scale everything if too wide
            scale_factor = 1.0
            if total_width > self.VIDEO_WIDTH * 0.9:
                scale_factor = (self.VIDEO_WIDTH * 0.9) / total_width
                base_char_size = int(base_char_size * scale_factor)
                char_spacing = int(char_spacing * scale_factor)
                space_width = int(space_width * scale_factor)
                total_width = int(total_width * scale_factor)
                char_positions = [
                    (int(pos[0] * scale_factor), int(pos[1] * scale_factor)) if pos is not None else None
                    for pos in char_positions
                ]

            # Center the text horizontally
            x_offset = (self.VIDEO_WIDTH - total_width) // 2

            # Build FFmpeg command
            cmd = ["ffmpeg", "-y"]

            # Add input files for characters (excluding spaces)
            for _, path in valid_chars:
                if path is not None:
                    cmd.extend(["-i", path])

            # Construct the complex filter
            filter_parts = []
            filter_parts.append(f"color=black:s={self.VIDEO_WIDTH}x{self.VIDEO_HEIGHT}:d={self.VIDEO_DURATION}:r={self.FPS}[bg];")

            # Initialize the overlay chain
            current = "bg"
            input_index = 0

            for i, ((char_index, path), position) in enumerate(zip(valid_chars, char_positions)):
                if path is not None and position is not None:
                    rel_x, char_width = position
                    x_pos = x_offset + rel_x
                    y_pos = (self.VIDEO_HEIGHT - base_char_size) // 2

                    # Scale and position each character
                    filter_parts.append(
                        f"[{input_index}:v]scale={base_char_size}:{base_char_size},setsar=1,format=gbrp[s{char_index}];"
                    )
                    filter_parts.append(
                        f"color=black@0:s={self.VIDEO_WIDTH}x{self.VIDEO_HEIGHT}:d={self.VIDEO_DURATION}[tmp{char_index}];"
                    )
                    filter_parts.append(
                        f"[tmp{char_index}][s{char_index}]overlay=x={x_pos}:y={y_pos}:format=auto[overlay{char_index}];"
                    )
                    filter_parts.append(
                        f"[{current}][overlay{char_index}]blend=all_mode='screen':shortest=1[blend{char_index}];"
                    )
                    current = f"blend{char_index}"
                    input_index += 1  # Increment input index only for non-space characters

            # Remove the trailing semicolon from the last filter part if necessary
            if filter_parts[-1].endswith(';'):
                filter_parts[-1] = filter_parts[-1][:-1]

            # Final assembly of the FFmpeg command
            filter_complex = "".join(filter_parts)
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", f"[{current}]",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-r", self.FPS,
                "-t", str(self.VIDEO_DURATION),
                "-pix_fmt", "yuv420p",
                f"generated_{text}.mp4"
            ])

            logger.debug("FFmpeg command: " + " ".join(cmd))

            # Execute the FFmpeg command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr}")
                raise RuntimeError(f"FFmpeg failed with error: {stderr}")

            logger.info("Video generation completed successfully")
            messagebox.showinfo("Success", f"Video generated successfully: generated_{text}.mp4")

        except Exception as e:
            logger.error(f"Error during video generation: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoTextGenerator(root)
    root.mainloop()