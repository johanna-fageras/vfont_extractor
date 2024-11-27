import os
import zipfile
from flask import Flask, render_template, request, send_file, redirect, url_for
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

app = Flask(__name__)

# Upload and output folders
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def sanitize_filename(name):
    """Sanitize filename to remove invalid characters."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)

def generate_static_fonts(variable_font_path, output_folder):
    """Generate static fonts from a variable font."""
    # Load the variable font
    font = TTFont(variable_font_path)
    
    # Extract the 'fvar' table to get predefined instances
    fvar = font['fvar']
    named_instances = fvar.instances
    
    for instance in named_instances:
        # Get instance name and coordinates
        instance_name_id = instance.subfamilyNameID
        instance_name_str = font['name'].getName(instance_name_id, 3, 1).toUnicode()
        coordinates = instance.coordinates

        # Build a detailed name including all axis values
        axis_values = []
        for axis_tag, value in coordinates.items():
            axis_values.append(f"{axis_tag}={int(value) if value.is_integer() else value:.2f}")
        detailed_name = f"{instance_name_str}_" + "_".join(axis_values)
        detailed_name = sanitize_filename(detailed_name)
        
        # Create a static font for this instance
        static_font = instancer.instantiateVariableFont(font, coordinates)
        
        # Save the static font
        output_path = os.path.join(output_folder, f"{detailed_name}.ttf")
        static_font.save(output_path)
        print(f"Generated static font: {output_path}")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return redirect(url_for("index"))
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return redirect(url_for("index"))
    
    # Save uploaded file
    variable_font_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(variable_font_path)
    
    # Clear the output folder
    for file in os.listdir(OUTPUT_FOLDER):
        os.remove(os.path.join(OUTPUT_FOLDER, file))
    
    # Generate static fonts
    generate_static_fonts(variable_font_path, OUTPUT_FOLDER)
    
    # Create a zip archive of the output folder
    zip_path = os.path.join(OUTPUT_FOLDER, "static_fonts.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                if file != "static_fonts.zip":
                    zipf.write(os.path.join(root, file), file)
    
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)