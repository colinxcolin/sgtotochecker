   
import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import re

# 1. Initialize the OCR Reader (English)
# Use gpu=False if you don't have an NVIDIA graphics card
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

st.set_page_config(page_title="SG Smart Toto Scanner", layout="centered")

# 1. Custom CSS for that "Special SG" look (Same as before)
st.markdown("""
    <style>
    .sg-badge {
        background-color: #ED1B24;
        color: white;
        padding: 2px 10px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 1.3em;
        display: inline-block;
        margin-right: 8px;
    }
    .instruction-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ED1B24;
        margin-bottom: 20px;
        font-size: 0.95em;
        color: #31333F; /* Standard Streamlit text color */
    }
    </style>
    """, unsafe_allow_html=True)
    
    
# 2. TITLE & INITIAL HOOK
st.markdown('<h1><span class="sg-badge">SG</span> TOTO Scanner</h1>', unsafe_allow_html=True)
st.write("**Tired of checking your TOTO tickets line by line? Try me!**")

# 3. THE GUIDE (Placed explicitly BEFORE the camera)
st.markdown("""
<div class="instruction-card">
    <b>Step-by-Step Guide:</b><br>
    1. Use your camera to take a picture of your ticket<br>
    2. Confirm our OCR detects your number correctly<br>
    3. Confirm if the TOTO winning numbers are correct<br>
    4. Match!
</div>
""", unsafe_allow_html=True)

# 4. THE CAMERA FRAME (Appears below the guide)
img_file = st.camera_input("Scan your ticket")

if img_file:
    st.success("✅ Ticket captured! Scroll down to verify numbers.")
    # Your OCR logic will trigger here
    
    
    
    
    
def preprocess_image(image_bytes):
    # Convert bytes to numpy array for OpenCV
    file_bytes = np.asarray(bytearray(image_bytes.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # Pre-processing for better OCR accuracy
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast and apply Threshold (B&W)
    # This helps distinguish '8' from '6' or 'B'
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return img, thresh

if img_file:
    # 3. Process Image
    original, processed = preprocess_image(img_file)
    
    # Show the "Cleaned" version to the user for transparency
    with st.expander("See what the AI sees (Processed Image)"):
        st.image(processed, caption="High-Contrast B&W")

    # 4. Perform OCR
    with st.spinner("Reading numbers..."):
        results = reader.readtext(processed)
        
        # Extract only the numbers found in the text
        all_text = " ".join([res[1] for res in results])
        # Find all 1 or 2 digit numbers (Toto numbers are 1-49)
        detected_numbers = re.findall(r'\b\d{1,2}\b', all_text)
        # Filter to keep only valid Toto numbers (1-49)
        valid_numbers = sorted(list(set([int(n) for n in detected_numbers if 1 <= int(n) <= 49])))

    # 5. User Verification (The "Double Check" Box)
    st.subheader("Verify Scanned Numbers")
    st.info("The AI might make mistakes. Please tap below to correct any numbers.")
    
    # We use a data_editor so the user can literally type over the mistakes
    final_numbers = st.data_editor(
        [valid_numbers], 
        num_rows="always",
        use_container_width=True
    )

    if st.button("Check Winnings"):
        user_picks = final_numbers[0]
        st.success(f"Checking these numbers: {user_picks}")
        # Phase 3 (Scraping logic) would be triggered here