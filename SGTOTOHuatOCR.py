   
import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import re

# 1. Initialize the OCR Reader (English)
# Use gpu=False if you don't have an NVIDIA graphics card
@st.cache_resource






def update_visitor_count():
    # Replace 'YOUR_API_KEY' with the actual key they gave you
    url = "https://api.counterapi.dev/v2/colinxcolins-team-2675/sgtotohuatchecker/up"
    headers = {"Authorization": "Bearer ut_WMBjN5tXKrNjLWyppZqGvOdtgq7mkCx380Gm5oqT"}
    
    try:
        # This sends the 'up' command to increase the count by 1
        response = requests.get(url, headers=headers)
        data = response.json()
        return data['count']
    except:
        return "0000" # Fallback if API is down


def handle_counter():
    # 1. Setup your API info
    namespace = "colinxcolins-team-2675"
    id = "sgtotohuatchecker"
    key = "ut_WMBjN5tXKrNjLWyppZqGvOdtgq7mkCx380Gm5oqT" # Replace with your actual key
    headers = {"Authorization": f"Bearer {key}"}
    
    # 2. Check if this is a new session (first time loading the page)
    if 'has_visited' not in st.session_state:
        # User just arrived! Increment the count.
        url = f"https://api.counterapi.dev/v2/{namespace}/{id}/up"
        st.session_state['has_visited'] = True
    else:
        # User is already here, just get the current number.
        url = f"https://api.counterapi.dev/v2/{namespace}/{id}"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        return response.json()['count']
    except Exception:
        return "000000" # Fallback if API fails


def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

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


    
# 3. Preprocessing Function
def preprocess_image(img_file):
    # Use .getvalue() instead of .read() to avoid empty buffer issues
    file_bytes = np.asarray(bytearray(img_file.getvalue()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img, thresh

    
    
# 4. Main App Logic (Combined into ONE block)
img_file = st.camera_input("Scan your ticket")

if img_file:
    st.success("✅ Ticket captured!")
    
    # Only "UP" the counter if we haven't done it this session
    if 'has_updated_count' not in st.session_state:
        update_visitor_count() # The /up call
        st.session_state['has_updated_count'] = True
  
    # Process Image
    original, processed = preprocess_image(img_file)
    
    with st.expander("See what the AI sees (Processed Image)"):
        st.image(processed, caption="High-Contrast B&W")

    # Perform OCR
    with st.spinner("Reading numbers..."):
        results = reader.readtext(processed)
        all_text = " ".join([res[1] for res in results])
        detected_numbers = re.findall(r'\b\d{1,2}\b', all_text)
        valid_numbers = sorted(list(set([int(n) for n in detected_numbers if 1 <= int(n) <= 49])))

    st.subheader("Verify Scanned Numbers")
    st.info("The AI might make mistakes. Please tap below to correct any numbers.")
    
    final_numbers = st.data_editor(
        [valid_numbers], 
        num_rows="always",
        use_container_width=True
    )

    if st.button("Check Winnings - In progress"):
        user_picks = final_numbers[0]
        st.success(f"Checking these numbers: {user_picks}")


mycount = handle_counter()
# Format the count to look like a 6-digit odometer
formatted_count = str(mycount).zfill(6)

# Display at the bottom (near your version/credits)
st.markdown(f"""
    <div style='text-align: center; margin-top: 20px;'>
        <p style='margin-bottom: 5px; font-size: 0.7rem; color: gray;'>VISITOR COUNT</p>
        <span class='visitor-counter'>{formatted_count}</span>
    </div>
""", unsafe_allow_html=True)

# 5. Footer
st.divider()
st.markdown("<div style='text-align: center; color: gray; font-size: 0.7rem;'> v1.0.2 (Works in progress) | Developed by satayfish </div>", unsafe_allow_html=True)







