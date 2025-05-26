"""
Script to create sample button images
For actual use, replace with images captured from Claude Desktop.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_button_image(text, width, height, filename):
    """Create a simple button image"""
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw button border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=2)
    
    # Add text (using default font)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Center text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    
    # Save
    assets_dir = 'assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    filepath = os.path.join(assets_dir, filename)
    img.save(filepath)
    print(f"Created: {filepath}")

def main():
    print("Creating sample button images...")
    print("Note: These are reference samples. Replace with actual captures from Claude Desktop for real use.")
    
    # Create sample images
    buttons = [
        ("Continue", 150, 60, "continue_button.png"),
        ("Projects", 100, 40, "projects_button.png"),
        ("Claude hit the maximum length...", 600, 50, "max_length_message.png"),
        ("kido", 200, 50, "kido_button.png"),
        ("My Project", 200, 50, "project_button.png")
    ]
    
    for text, width, height, filename in buttons:
        create_button_image(text, width, height, filename)
    
    print("\nSample image creation complete!")
    print("For actual use, capture directly from Claude Desktop:")
    print("1. Use Win + Shift + S")
    print("2. Or run: python claude_desktop_automation.py --setup")

if __name__ == "__main__":
    # Check PIL/Pillow installation
    try:
        from PIL import Image, ImageDraw, ImageFont
        main()
    except ImportError:
        print("PIL/Pillow is not installed.")
        print("To install: pip install Pillow")
        print("\nOr manually capture images:")
        print("- Use Win + Shift + S")
        print("- Save as PNG files in assets folder")
