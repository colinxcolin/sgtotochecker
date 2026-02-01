   
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
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    # NEW: Upscale the image by 2x
    # Change fx=2 to fx=3 to make the image 3x bigger
    img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Try changing the 150 to a higher number like 180 or 200 
    # to make it less sensitive to the grey logo/watermark    
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img, thresh

    


# UPDATED Grouping Logic
def group_by_system(valid_data, target):
    final_sets = []
    if not valid_data: return []

    temp_numbers = []
    for item in valid_data:
        temp_numbers.append(item['val'])
        
        # Once we hit the target count for that system, save the row
        if len(temp_numbers) == target:
            final_sets.append(sorted(list(set(temp_numbers))))
            temp_numbers = []
            
    # If there's a leftover (like a half-finished row), add it too
    if temp_numbers:
        final_sets.append(sorted(list(set(temp_numbers))))
        
    return final_sets
   



def process_ticket_logic(ocr_results, target_count):
    valid_data = []
    
    for (bbox, text, prob) in ocr_results:
        # 1. CLEANING: Remove the 'A.', 'B.' etc. 
        # We look for numbers 1-49. This automatically ignores single letters.
        nums = re.findall(r'\b\d{1,2}\b', text)
        
        for n in nums:
            val = int(n)
            if 1 <= val <= 49:
                y_mid = (bbox[0][1] + bbox[2][1]) / 2
                valid_data.append({'val': val, 'y': y_mid})
                
    if not valid_data: return []
    
    # Sort top-to-bottom
    valid_data.sort(key=lambda k: k['y'])
    
    # 2. SMART GROUPING
    final_sets = []
    buffer_set = []
    
    if valid_data:
        # Group numbers into physical lines based on vertical proximity
        lines = []
        current_line = [valid_data[0]['val']]
        last_y = valid_data[0]['y']
        
        for i in range(1, len(valid_data)):
            # If the vertical gap is small, it's the same physical line
            if abs(valid_data[i]['y'] - last_y) < 35:
                current_line.append(valid_data[i]['val'])
            else:
                lines.append(current_line)
                current_line = [valid_data[i]['val']]
            last_y = valid_data[i]['y']
        lines.append(current_line)

        # 3. CHUNKING BY SYSTEM
        # This handles the 6+1 (System 7) or 6+2 (System 8) 
        temp_bet = []
        for line in lines:
            temp_bet.extend(line)
            # If we hit the target (7, 8, or 12), save it as one row
            if len(temp_bet) >= target_count:
                # remove duplicates and sort
                final_sets.append(sorted(list(set(temp_bet))))
                temp_bet = []
        
        # Add leftovers if they look like a valid bet
        if len(temp_bet) >= 6:
            final_sets.append(sorted(list(set(temp_bet))))
            
    return final_sets
    
    
    
   



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
    return {"numbers": [11, 13, 16, 31, 42, 48], "additional": 21, "date": "1 Feb 2026"}
    
    

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


# --- 1. UI Selection for System Type ---
st.subheader("1. Configure Your Bet")
system_type = st.selectbox(
    "What System are you scanning?", 
    ["Quickpick (6)", "System 7", "System 8", "System 9", "System 10", "System 11", "System 12"]
)
# Extract the number from the string (e.g., "System 7" -> 7)
target_count = int(re.search(r'\d+', system_type).group()) if "Ordinary" not in system_type else 6

    


tab1, tab2 = st.tabs(["📸 Camera", "📁 Upload Image"])

with tab1:
    
    # --- 2. Camera with Overlay Guidelines ---
    st.markdown("""
    <style>
    /* This creates a red guideline box over the camera widget */
    div[data-testid="stCameraInput"]::before {
        content: "";
        position: absolute;
        top: 20%;
        left: 10%;
        width: 80%;
        height: 60%;
        border: 2px dashed #ED1B24;
        border-radius: 10px;
        pointer-events: none; /* Allows you to still click the 'Take Photo' button */
        z-index: 99;
    }
    </style>
    <p style='color: #ED1B24; font-size: 0.8rem; text-align: center;'>Align ticket within the red box for best results</p>
""", unsafe_allow_html=True)

    camera_img = st.camera_input("Take a photo of your ticket")

with tab2:
    uploaded_img = st.file_uploader("Or select a ticket from your computer", type=['jpg', 'jpeg', 'png'])

# Use whichever one has data
img_file = camera_img if camera_img else uploaded_img


# --- 3. UI LAYOUT & MAIN LOGIC ---

# ONLY ONE camera input here
#img_file = st.camera_input("Take a photo of your ticket")

if img_file:
    st.success("✅ Ticket captured!")
    
    original, processed = preprocess_image(img_file)
    
    with st.expander("See what the AI sees"):
        st.image(processed, caption="High-Contrast B&W")

    # B. Perform OCR (Your GitHub logic + My Spatial Logic)
    with st.spinner(f"Scanning for {target_count} numbers..."):
        
        results = reader.readtext(
            processed,
            # allowlist REMOVED so AI doesn't force 'A' to be '4'
            detail=1, 
            paragraph=False,
            # These settings are great for your high-contrast images:
            contrast_ths=0.05, 
            adjust_contrast=0.7, 
            text_threshold=0.5, 
            low_text=0.3 
        )
        
        # Collect ALL valid numbers found anywhere
        valid_data = []
        img_h, img_w = processed.shape[:2]

        for (bbox, text, prob) in results:
            x_min = bbox[0][0]
            # Ignore the left-most 20% of the image
            if x_min < (processed.shape[1] * 0.20):
                continue
            
            # Now extract only real digits            
            nums = re.findall(r'\b\d{1,2}\b', text)
            
            for n in nums:
                val = int(n)
                if 1 <= val <= 49:
                    # Capture the vertical center (y) to handle the hanging 44/49
                    y_center = (bbox[0][1] + bbox[2][1]) / 2
                    valid_data.append({'val': val, 'y': y_center})

        # --- 4. THE SYSTEM 7 BUCKET LOGIC ---
        # Sort all numbers found from the top of the ticket to the bottom
        valid_data.sort(key=lambda k: k['y'])
        
        final_sets = []
        current_bucket = []
        
        for item in valid_data:
            # Avoid duplicate detection
            if item['val'] not in current_bucket:
                current_bucket.append(item['val'])
            
            # Once we have 7 numbers, we have completed one "System 7" bet
            if len(current_bucket) == target_count:
                final_sets.append(sorted(current_bucket))
                current_bucket = []
        
        # Add any remaining numbers (must have at least 6 to be a valid bet)
        if len(current_bucket) >= 6:
            final_sets.append(sorted(current_bucket))



     
            
# --- 4. VERIFICATION & BALL DISPLAY ---
    if final_sets:
        st.subheader("2. Verify & Check")
        edited_sets = st.data_editor(final_sets, num_rows="dynamic", use_container_width=True)
        
        if st.button("Check Winnings 💰"):
            draw_results = get_latest_toto_results()
            winning_nos = sorted(list(draw_results['numbers']))
            bonus_no = draw_results['additional']

            # --- THE FIXED BALL DISPLAY ---
            balls_html = []
            # Red Balls
            for n in winning_nos:
                balls_html.append(f'<div style="background:#ED1B24; color:white; border-radius:50%; width:50px; height:50px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:bold; margin:5px;">{n}</div>')
            # Blue Ball
            balls_html.append(f'<div style="background:#0052A4; color:white; border-radius:50%; width:50px; height:50px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:bold; margin:5px;">{bonus_no}</div>')
            
            # Join them into one row
            full_display = f'<div style="display:flex; justify-content:center; flex-wrap:wrap;">{"".join(balls_html)}</div>'
            st.markdown(full_display, unsafe_allow_html=True)
            
            # --- COMPARISON LOGIC ---
            for idx, row in enumerate(edited_sets):
                matches = set(row).intersection(set(winning_nos))
                count = len(matches)
                is_bonus = bonus_no in row
                
                label = f"Row {chr(65+idx)}"
                if count >= 3:
                    st.success(f"✅ {label}: {count} matches" + (" + Bonus!" if is_bonus else ""))
                else:
                    st.info(f"❌ {label}: {count} matches")
            st.balloons()
            
    else:
        # If final_sets is empty, it means process_ticket_logic returned nothing
        st.error("No numbers detected. Ensure the ticket is inside the guide box and well-lit.")
    
    



    


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







