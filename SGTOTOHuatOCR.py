   
import streamlit as st
import requests
import cv2
import numpy as np
import easyocr

from PIL import Image
import re


# Replace with your actual key if you want to use the Private mode
API_KEY = "ut_WMBjN5tXKrNjLWyppZqGvOdtgq7mkCx380Gm5oqT"
NAMESPACE = "colinxcolins-team-2675"
KEY_ID = "sgtotohuatchecker"


@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()



def preprocess_image(img_file):
    file_bytes = np.asarray(bytearray(img_file.getvalue()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img, thresh
    

def process_ticket_logic(ocr_results):
    valid_data = []
    for (bbox, text, prob) in ocr_results:
        clean_text = "".join(filter(str.isdigit, text))
        if clean_text and 1 <= int(clean_text) <= 49:
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            valid_data.append({'val': int(clean_text), 'y': y_center})
    if not valid_data: return []
    valid_data.sort(key=lambda k: k['y'])
    toto_sets = []
    current_set = [valid_data[0]['val']]
    last_y = valid_data[0]['y']
    line_threshold = 35 
    for i in range(1, len(valid_data)):
        gap = valid_data[i]['y'] - last_y
        if gap < line_threshold:
            current_set.append(valid_data[i]['val'])
        else:
            toto_sets.append(sorted(list(set(current_set))))
            current_set = [valid_data[i]['val']]
        last_y = valid_data[i]['y']
    toto_sets.append(sorted(list(set(current_set))))
    return [s for s in toto_sets if len(s) >= 6]





def update_scan_counter():
    up_url = f"https://api.counterapi.dev/v2/{NAMESPACE}/{KEY_ID}/up"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(up_url, headers=headers, timeout=5)
        return response.json()['data']['up_count']
    except: return "000000"



def get_latest_toto_results():
    # Placeholder: In a real scenario, this scrapes SG Pools. 
    # For now, it returns dummy data to prevent errors.
    return {"numbers": [1, 12, 23, 34, 45, 46], "additional": 7, "date": "1 Feb 2026"}
    
    

st.set_page_config(page_title="SG Smart Toto Scanner", layout="centered")

# Custom CSS to shrink text and enlarge the camera
st.markdown("""
    <style>
    
    h1 {
    font-size: 2rem !important;
    margin-bottom: 5px !important;
    padding-top: 0px !important;
    }


    /* 1. Make all base text smaller */
    html, body, [class*="st-"] {
        font-size: 0.8rem !important;
    }
    
    /* 2. Make the SG Badge smaller and neater */
    .sg-badge {
        background-color: #ED1B24;
        color: white;
        padding: 1px 6px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 0.7rem;
        vertical-align: middle;
    }

    /* 3. Force the Camera Frame to be wider/larger */
    div[data-testid="stCameraInput"] {
        width: 100% !important;
        max-width: 800px !important;
    }
    
    /* 4. Shrink the instruction card text */
    .instruction-card {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #ED1B24;
        font-size: 0.8rem;
        line-height: 1.3;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
# 2. TITLE & INITIAL HOOK
st.markdown('<h1><span class="sg-badge">SG</span> TOTO Scanner</h1>', unsafe_allow_html=True)
st.markdown("<p style='margin-top: -15px; font-weight: bold;'>Tired of checking your TOTO tickets line by line? Try me!</p>", unsafe_allow_html=True)



# 3. THE GUIDE (Placed explicitly BEFORE the camera)
st.markdown("""
<div class="instruction-card">
    <b>Step-by-Step Guide:</b><br>
    1. 💡 Ensure you are in a <b>well-lit</b> area.<br>
    2. 📸 Allow camera and snap your toto ticket. <b>Bring further</b> for better focus.<br>
    3. ✅ <b>Confirm</b> TOTO ticket numbers with AI scanner (🔍double check!🔍)<br>
    4. 🏆 <b>[Work in Progress]</b> Match the right TOTO winning numbers to HUAT 💰. <br>
</div>
""", unsafe_allow_html=True)




# --- 3. UI LAYOUT & MAIN LOGIC ---

# ONLY ONE camera input here
img_file = st.camera_input("Take a photo of your ticket")

if img_file:
    st.success("✅ Ticket captured!")
    
    # A. Processing
    original, processed = preprocess_image(img_file)
    
    with st.expander("See what the AI sees"):
        st.image(processed, caption="High-Contrast B&W")

    # B. Perform OCR (Your GitHub logic + My Spatial Logic)
    with st.spinner("Reading numbers row-by-row..."):
        results = reader.readtext(processed)
        
        valid_data = []
        for res in results:
            bbox = res[0]
            text = res[1]
            
            # Use your old Regex to find numbers 1-49
            detected = re.findall(r'\b\d{1,2}\b', text)
            for n in detected:
                num = int(n)
                if 1 <= num <= 49:
                    # Calculate Y-center for grouping
                    y_center = (bbox[0][1] + bbox[2][1]) / 2
                    valid_data.append({'val': num, 'y': y_center})

        # C. Grouping (The System 7/8 Logic)
        final_sets = []
        if valid_data:
            # Sort all found numbers by their vertical position
            valid_data.sort(key=lambda k: k['y'])
            
            current_set = [valid_data[0]['val']]
            last_y = valid_data[0]['y']
            line_threshold = 40 # Increased slightly to handle watermark gaps
            
            for i in range(1, len(valid_data)):
                gap = valid_data[i]['y'] - last_y
                if gap < line_threshold:
                    current_set.append(valid_data[i]['val'])
                else:
                    final_sets.append(sorted(list(set(current_set))))
                    current_set = [valid_data[i]['val']]
                last_y = valid_data[i]['y']
            
            final_sets.append(sorted(list(set(current_set))))

    # D. Display in the Data Editor
    if final_sets:
        st.subheader("Verify Scanned Numbers")
        # Filter out rows with fewer than 6 numbers (likely noise/dates)
        filtered_sets = [s for s in final_sets if len(s) >= 6]
        
        edited_sets = st.data_editor(
            filtered_sets, 
            num_rows="dynamic", 
            use_container_width=True
        )
        
        if st.button("Check Winnings"):
            # Comparison logic goes here...
            st.balloons()
    else:
        st.error("No numbers detected. The watermark might be too dark!")







# --- 4. FOOTER & VISITOR COUNT ---

display_count = st.session_state.get('scan_val', "000000")
formatted_count = str(display_count).zfill(6)

st.markdown(f"""
    <div style='text-align: center;'>
        <p style='color: gray; font-size: 0.8rem;'>TOTAL TICKETS SCANNED</p>
        <span class="odometer">{formatted_count}</span>
    </div>
""", unsafe_allow_html=True)




# 5. Footer
st.divider()
st.markdown("<div style='text-align: center; color: gray; font-size: 0.7rem;'> v1.0.3 (Works in progress) | Developed by satayfish </div>", unsafe_allow_html=True)







