import os
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime

app = Flask(__name__)

class OregonPlateGenerator:
    def __init__(self):
        # Define plate configurations
        self.plate_config = {
            'standard': {
                'name': 'Standard Oregon Tree',
                'image_path': 'static/images/oregon_standard_clean.png',
                'text_color': '#1B365D',  # Dark blue color from the image
                'text_position': (490, 180),  # Center position for license text 475,240
                'font_size': 200, #original 85
                'letter_spacing': 8, # original 8
                'max_chars': 10  # original 7
            }
        }
        
        # Create directories if they don't exist
        os.makedirs('static/images', exist_ok=True)
        os.makedirs('static/output', exist_ok=True)
        
        # Process the uploaded image to create clean base
        self.create_clean_base_image()
    
    def create_clean_base_image(self):
        """
        Create a clean base image by removing the '000 BBB' text from the original
        This would be done manually or with image editing tools in a real scenario
        For now, we'll simulate having a clean base
        """
        # In a real implementation, you would:
        # 1. Load the original Oregon plate image
        # 2. Use image inpainting or manual editing to remove "000 BBB"
        # 3. Save as clean base image
        
        # For demonstration, we'll create a template
        # You would replace this with the actual cleaned image
        try:
            # Try to load existing clean image
            base_img = Image.open('static/images/oregon_standard_clean.png')
        except FileNotFoundError:
            # Create a placeholder if the clean image doesn't exist
            self.create_placeholder_image()
    
    def create_placeholder_image(self):
        """Create a placeholder Oregon plate image"""
        # Create base image with Oregon plate dimensions (roughly 12" x 6")
        width, height = 950, 475
        img = Image.new('RGB', (width, height), '#E8F4F8')  # Light blue background
        draw = ImageDraw.Draw(img)
        
        # Draw border
        border_color = '#1B365D'
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=8)
        
        # Draw mountain silhouette at bottom
        mountain_points = [
            (0, height-80), (150, height-120), (300, height-100), 
            (450, height-140), (600, height-110), (750, height-130),
            (width, height-90), (width, height), (0, height)
        ]
        draw.polygon(mountain_points, fill='#2C5F7C')
        
        # Draw tree in center (simplified)
        tree_x, tree_y = width//2, height-120
        # Tree trunk
        draw.rectangle([tree_x-8, tree_y, tree_x+8, tree_y+40], fill='#4A6741')
        # Tree layers
        for i in range(3):
            y_offset = tree_y - 20 - (i * 25)
            size = 40 - (i * 5)
            draw.ellipse([tree_x-size, y_offset-size//2, tree_x+size, y_offset+size//2], fill='#5C8A58')
        
        # Add "Oregon" text at top
        try:
            font = ImageFont.truetype("arialbold.ttf", 48) # original = arial.tff
        except:
            font = ImageFont.load_default()
        
        text = "Oregon"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((width//2 - text_width//2, 40), text, fill=border_color, font=font)
        
        # Add mounting holes
        hole_positions = [(80, 80), (width-80, 80), (80, height-80), (width-80, height-80)]
        for x, y in hole_positions:
            draw.ellipse([x-15, y-15, x+15, y+15], fill='#000000')
        
        # Add month/year sticker areas
        draw.rectangle([80, height-150, 160, height-100], outline=border_color, width=3)
        draw.rectangle([width-160, height-150, width-80, height-100], outline=border_color, width=3)
        
        # Save the placeholder
        img.save('static/images/oregon_standard_clean.png')
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_plate(self, text, plate_type='standard'):
        """Generate license plate with custom text"""
        if plate_type not in self.plate_config:
            raise ValueError(f"Unknown plate type: {plate_type}")
        
        config = self.plate_config[plate_type]
        
        # Validate text
        text = text.upper().strip()
        if len(text) > config['max_chars']:
            text = text[:config['max_chars']]
        
        # Load base image
        try:
            base_img = Image.open(config['image_path'])
        except FileNotFoundError:
            self.create_placeholder_image()
            base_img = Image.open(config['image_path'])
        
        # Create a copy to work with
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            # Try different font paths for different systems
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",  # Windows
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "arial.ttf"  # Local
            ]
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, config['font_size'])
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Calculate text position with letter spacing
        if config.get('letter_spacing', 0) > 0:
            self.draw_text_with_spacing(draw, text, config['text_position'], 
                                      font, config['text_color'], config['letter_spacing'])
        else:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = config['text_position'][0] - text_width // 2
            y = config['text_position'][1] - text_height // 2
            
            draw.text((x, y), text, fill=self.hex_to_rgb(config['text_color']), font=font)
        
        return img
    
    def draw_text_with_spacing(self, draw, text, position, font, color, spacing):
        """Draw text with custom letter spacing"""
        x, y = position
        color_rgb = self.hex_to_rgb(color)
        
        # Calculate total width to center the text
        total_width = 0
        char_widths = []
        for char in text:
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            char_widths.append(char_width)
            total_width += char_width
        
        total_width += spacing * (len(text) - 1)
        
        # Start from center position minus half total width
        current_x = x - total_width // 2
        
        for i, char in enumerate(text):
            draw.text((current_x, y - 25), char, fill=color_rgb, font=font)  # Adjust y for vertical centering
            current_x += char_widths[i] + spacing

# Initialize the plate generator
plate_generator = OregonPlateGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_plate():
    try:
        data = request.json
        text = data.get('text', 'SAMPLE')
        plate_type = data.get('plate_type', 'standard')
        
        # Generate the plate
        img = plate_generator.generate_plate(text, plate_type)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        
        # Convert to base64 for web display
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'filename': f'oregon_plate_{text}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<text>')
def download_plate(text):
    try:
        img = plate_generator.generate_plate(text)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        
        return send_file(img_bytes, 
                        mimetype='image/png',
                        as_attachment=True,
                        download_name=f'oregon_plate_{text}.png')
    
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)