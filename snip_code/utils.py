import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_barcode(data: str) -> BytesIO:
    """Generate a barcode image and return it as a BytesIO object."""
    EAN = barcode.get_barcode_class('ean13')
    ean = EAN(data, writer=ImageWriter())
    barcode_buffer = BytesIO()
    ean.write(barcode_buffer)
    barcode_buffer.seek(0)
    return barcode_buffer

def generate_label(data: str, item_info: dict, packaging_type_info: dict) -> BytesIO:
    """Generate a PDF label that includes item and packaging type information along with a barcode."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Draw item text on the label (if item info is provided)
    if item_info:
        c.drawString(100, 750, f"Item: {item_info['name']}")
        c.drawString(100, 735, f"Description: {item_info['description']}")
        c.drawString(100, 720, f"Dimensions: {item_info['length']} x {item_info['width']} x {item_info['height']}")
    
    # Draw packaging type text on the label
    c.drawString(100, 705, f"Packaging Type: {packaging_type_info['name']}")
    c.drawString(100, 690, f"Material: {packaging_type_info['material']}")
    c.drawString(100, 675, f"Weight: {packaging_type_info['weight']}")
    
    # Draw the barcode on the label
    barcode_buffer = generate_barcode(data)
    c.drawImage(barcode_buffer, 100, 600, width=200, height=100)  # Adjust size and position as needed
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
