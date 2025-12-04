"""
PDF Generator for Member Digital IDs
Generates PDF bundles with multiple member ID cards per page
"""

import os
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image
from flask import current_app


def generate_member_ids_pdf(members, layout='bundle', page_size='letter'):
    """
    Generate PDF with member ID cards arranged in pages
    
    Args:
        members: List of Member objects with digital_id_path
        layout: 'single' (1 per page), 'standard' (2 per page), 'bundle' (4 per page)
        page_size: 'letter' or 'a4'
    
    Returns:
        BytesIO object containing PDF data
    """
    # Set page size
    if page_size == 'a4':
        page_width, page_height = A4
    else:
        page_width, page_height = letter
    
    # Create PDF buffer
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    # ID card dimensions (from id_generator.py: 1016x640px)
    # Scale to fit on page
    id_width_px = 1016
    id_height_px = 640
    id_aspect_ratio = id_width_px / id_height_px
    
    # Calculate layout dimensions
    if layout == 'single':
        ids_per_page = 1
        cols = 1
        rows = 1
    elif layout == 'standard':
        ids_per_page = 2
        cols = 2
        rows = 1
    else:  # bundle
        ids_per_page = 4
        cols = 2
        rows = 2
    
    # Calculate margins and spacing
    margin = 0.5 * inch
    spacing = 0.3 * inch
    
    # Calculate available space
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)
    
    # Calculate card size based on layout
    if layout == 'single':
        card_width = available_width * 0.9
        card_height = card_width / id_aspect_ratio
    elif layout == 'standard':
        card_width = (available_width - spacing) / 2
        card_height = card_width / id_aspect_ratio
    else:  # bundle
        card_width = (available_width - spacing) / 2
        card_height = (available_height - spacing) / 2
    
    # Ensure card doesn't exceed available height
    if card_height > available_height:
        card_height = available_height * 0.9
        card_width = card_height * id_aspect_ratio
    
    # Filter members with digital IDs
    members_with_ids = [m for m in members if m.digital_id_path]
    
    if not members_with_ids:
        # Add a message page if no IDs
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(margin, page_height - margin - 50, "No Member IDs Available")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(margin, page_height - margin - 80, "No members have digital ID cards generated yet.")
        pdf.save()
        buffer.seek(0)
        return buffer
    
    # Process members in batches
    for page_idx in range(0, len(members_with_ids), ids_per_page):
        # Start new page (except first)
        if page_idx > 0:
            pdf.showPage()
        
        # Get members for this page
        page_members = members_with_ids[page_idx:page_idx + ids_per_page]
        
        # Draw front sides on this page
        for idx, member in enumerate(page_members):
            row = idx // cols
            col = idx % cols
            
            # Calculate position
            x = margin + col * (card_width + spacing)
            y = page_height - margin - (row + 1) * (card_height + spacing)
            
            # Draw front side
            front_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                'digital_ids',
                member.digital_id_path
            )
            
            if os.path.exists(front_path):
                try:
                    img = Image.open(front_path)
                    pdf.drawImage(
                        ImageReader(img),
                        x, y,
                        width=card_width,
                        height=card_height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception as e:
                    current_app.logger.error(f"Error loading front image for {member.member_id_number}: {e}")
                    # Draw placeholder
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(x, y + card_height/2, f"ID: {member.member_id_number}")
                    pdf.drawString(x, y + card_height/2 - 15, "Image not available")
            else:
                # Draw placeholder if file doesn't exist
                pdf.setFont("Helvetica", 10)
                pdf.drawString(x, y + card_height/2, f"ID: {member.member_id_number}")
                pdf.drawString(x, y + card_height/2 - 15, "Image not found")
        
        # Add back sides on next page (always separate page for clarity)
        if page_members:
            pdf.showPage()
            
            # Add page label
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(margin, page_height - margin + 20, "Back Sides")
            
            for idx, member in enumerate(page_members):
                row = idx // cols
                col = idx % cols
                
                # Calculate position (adjust for label)
                x = margin + col * (card_width + spacing)
                y = page_height - margin - 30 - (row + 1) * (card_height + spacing)
                
                # Draw back side
                back_filename = member.digital_id_path.replace('_front.png', '_back.png')
                back_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'digital_ids',
                    back_filename
                )
                
                if os.path.exists(back_path):
                    try:
                        img = Image.open(back_path)
                        pdf.drawImage(
                            ImageReader(img),
                            x, y,
                            width=card_width,
                            height=card_height,
                            preserveAspectRatio=True,
                            mask='auto'
                        )
                    except Exception as e:
                        current_app.logger.error(f"Error loading back image for {member.member_id_number}: {e}")
                        # Draw placeholder
                        pdf.setFont("Helvetica", 10)
                        pdf.drawString(x, y + card_height/2, f"ID: {member.member_id_number}")
                        pdf.drawString(x, y + card_height/2 - 15, "Back image not available")
                else:
                    # Draw placeholder if file doesn't exist
                    pdf.setFont("Helvetica", 10)
                    pdf.drawString(x, y + card_height/2, f"ID: {member.member_id_number}")
                    pdf.drawString(x, y + card_height/2 - 15, "Back image not found")
    
    # Save PDF
    pdf.save()
    buffer.seek(0)
    return buffer

