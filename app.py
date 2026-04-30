import streamlit as st
import pandas as pd
from datetime import datetime
import os
import torch 
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io
import traceback
import requests


# =========================
# GitHub Model Config
# =========================
MODEL_URL = "https://github.com/usmaniwho/Cat-Breed-Data-Entry/releases/download/v1.0/resnet50-model-augmentation.pth"
MODEL_PATH = "resnet50-model-augmentation.pth"


# =========================
# Safe Model Download
# =========================
def download_model():
    """Safely download model from GitHub Releases"""

    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 10000:
        return MODEL_PATH

    st.info("📥 Downloading model from GitHub Releases...")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(
            MODEL_URL,
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=60
        )

        # 🚨 Check if GitHub returned HTML instead of file
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise Exception("GitHub returned HTML page instead of model file. Check release URL.")

        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")

        # Save file
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 🚨 Validate file size (prevents corrupted downloads)
        if os.path.getsize(MODEL_PATH) < 10000:
            raise Exception("Downloaded file is too small → likely corrupted")

        st.success("✅ Model downloaded successfully!")
        return MODEL_PATH

    except Exception as e:
        st.error(f"❌ Model download failed: {e}")
        return None


# =========================
# Load Model (Safe + PyTorch 2.6 fix)
# =========================
@st.cache_resource
def load_model(cat_classes):
    """Load trained ResNet50 model safely"""

    model_path = download_model()
    if model_path is None:
        return None

    # Define model architecture
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(cat_classes))

    try:
        # 🔥 FIX for PyTorch 2.6
        checkpoint = torch.load(
            model_path,
            map_location="cpu",
            weights_only=False
        )

        # Handle different checkpoint formats
        if isinstance(checkpoint, dict):
            if "model" in checkpoint:
                checkpoint = checkpoint["model"]
            elif "state_dict" in checkpoint:
                checkpoint = checkpoint["state_dict"]

        # Fix: Remap keys from fc.0.weight -> fc.weight and fc.0.bias -> fc.bias
        # This handles checkpoints saved with nn.Sequential structure
        state_dict = {}
        for key, value in checkpoint.items():
            if key.startswith("fc.0."):
                new_key = key.replace("fc.0.", "fc.")
                state_dict[new_key] = value
            elif key.startswith("fc."):
                # Skip other fc.* keys that don't match our simple fc layer
                continue
            else:
                state_dict[key] = value

        # Load with strict=False to ignore mismatched keys
        model.load_state_dict(state_dict, strict=False)
        model.eval()

        return model

    except Exception as e:
        st.error(f"❌ Model loading failed: {e}")
        return None

st.title("🐱 Cat Data Entry")

# =========================
# Model Configuration
# =========================
CAT_CLASSES = [
    "Abyssinian", "Bengal", "Birman", "Bombay", "British_Shorthair",
    "Egyptian_Mau", "Maine_Coon", "Persian", "Ragdoll", "Russian_Blue",
    "Siamese", "Sphynx"
]

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def predict_breed(image_bytes):
    """Predict cat breed from image bytes"""
    model = load_model(CAT_CLASSES)
    
    # Handle model loading failure
    if model is None:
        raise Exception("Failed to load model. Please refresh the page and try again.")
    
    # Load and preprocess image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_tensor = transform(image).unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)
        
        # Get top prediction
        top_idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0, top_idx].item()
        
        predicted_breed = CAT_CLASSES[top_idx]
        
        # Get top 3 for display
        top3 = torch.topk(probs, 3)
        top_predictions = []
        for idx, prob in zip(top3.indices[0], top3.values[0]):
            top_predictions.append({
                "breed": CAT_CLASSES[idx],
                "confidence": float(prob)
            })
    
    return predicted_breed, confidence, top_predictions

# Initialize session state for data
if 'data_df' not in st.session_state:
    st.session_state.data_df = pd.DataFrame(columns=[
        "Date", "Sample ID", "City", "Clinic", "Owner ID", "Age", 
        "Age Group", "Sex", "Indoor/Outdoor", "Cat Breed", "Ticks", "Organ", "Number", "Size"
    ])

# Initialize session state for uploaded data
if 'uploaded_data_df' not in st.session_state:
    st.session_state.uploaded_data_df = None

# Initialize session state for prediction results (for reactive updates)
if 'predicted_breed' not in st.session_state:
    st.session_state.predicted_breed = ""
if 'confidence' not in st.session_state:
    st.session_state.confidence = 0.0
if 'top_predictions' not in st.session_state:
    st.session_state.top_predictions = []
if 'uploaded_image_bytes' not in st.session_state:
    st.session_state.uploaded_image_bytes = None

# Delete previous session CSV files at app startup
csv_files = ["cat_data.csv", "cat_data_uploaded.csv"]
for csv_file in csv_files:
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
        except Exception as e:
            pass  # Ignore errors - file may be in use

# File handling options
st.header("📁 Data File Option")
file_option = st.radio(
    "Choose an option:",
    ["Create new file", "Upload existing file"],
    horizontal=True
)

data_file = "cat_data.csv"

# Store uploaded data separately in session state (preserves original uploaded data)
if file_option == "Upload existing file":
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            st.session_state.uploaded_data_df = pd.read_csv(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            st.session_state.uploaded_data_df = None
    else:
        st.info("Please upload a file or choose 'Create new file'")

# =========================
# Cat Image Upload and Breed Prediction (OUTSIDE form for reactive updates)
# =========================
#st.header("🐱 Cat Image & Breed Prediction")

# Image uploader OUTSIDE the form - allows immediate reactive updates
uploaded_image = st.file_uploader("Upload Cat Image", type=["jpg", "jpeg", "png"])

# Process image when uploaded (reactive mode)
if uploaded_image is not None:
    # Display uploaded image
    image_bytes = uploaded_image.getvalue()
    st.image(image_bytes, caption="Uploaded Cat Image", width=200)
    
    # Store the image bytes in session state
    st.session_state.uploaded_image_bytes = image_bytes
    
    # Predict breed with error handling
    try:
        predicted_breed, confidence, top_predictions = predict_breed(image_bytes)
        
        # Store in session state for use in form
        st.session_state.predicted_breed = predicted_breed
        st.session_state.confidence = confidence
        st.session_state.top_predictions = top_predictions
        
        # Show top 3 predictions
        st.write("**Top Predictions:**")
        for pred in top_predictions:
            st.write(f"- {pred['breed']}: {pred['confidence']*100:.1f}%")
        
        st.success(f"Predicted Breed: **{predicted_breed}** ({confidence*100:.1f}% confidence)")
    except Exception as e:
        st.error(f"Prediction error: {e}")
        st.error(traceback.format_exc())
elif st.session_state.uploaded_image_bytes is not None:
    # Show previously uploaded image if it exists
    st.image(st.session_state.uploaded_image_bytes, caption="Uploaded Cat Image", width=200)
    if st.session_state.predicted_breed:
        st.write("**Top Predictions:**")
        for pred in st.session_state.top_predictions:
            st.write(f"- {pred['breed']}: {pred['confidence']*100:.1f}%")
        st.success(f"Predicted Breed: **{st.session_state.predicted_breed}** ({st.session_state.confidence*100:.1f}% confidence)")

# Data entry form
st.header("📝 Enter Cat Data")

with st.form("data_form", clear_on_submit=True):
    sample_id = st.text_input("Sample ID")
    city = st.text_input("City")
    clinic = st.text_input("Clinic")
    owner = st.text_input("Owner ID")
    age = st.number_input("Cat Age", min_value=0, step=1, format="%d")

    age_group = st.selectbox("Age Group", ["Kitten","Young","Adult"])
    sex = st.selectbox("Sex", ["M","F"])
    indoor = st.selectbox("Indoor/Outdoor", ["Indoor","Outdoor"])

    # =========================
    # Cat Breed (use prediction from session state)
    # =========================
    #st.markdown("---")
    
    # Use the predicted breed from session state (set by image upload above)
    predicted_breed = st.session_state.predicted_breed
    current_breed = st.selectbox(
        "Cat Breed (editable)",
        CAT_CLASSES,
        index=CAT_CLASSES.index(predicted_breed) if predicted_breed in CAT_CLASSES else 0
    )
    
    # Show prediction confidence if available
    if st.session_state.confidence > 0:
        st.caption(f"Model confidence: {st.session_state.confidence*100:.1f}%")

    # =========================
    # Ticks Information
    # =========================
    #st.markdown("---")
    ticks = st.selectbox("Ticks Presence", ["Positive","Negative"])

    organ = number = size = ""

    if ticks == "Positive":
        organ = st.text_input("Organ of Tick")
        number = st.text_input("Number of Ticks")
        size = st.text_input("Size of Ticks")
    
    submit = st.form_submit_button("Save Data")

if submit:
    row = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Sample ID": sample_id,
        "City": city,
        "Clinic": clinic,
        "Owner ID": owner,
        "Age": age,
        "Age Group": age_group,
        "Sex": sex,
        "Indoor/Outdoor": indoor,
        "Cat Breed": current_breed,
        "Ticks": ticks,
        "Organ": organ,
        "Number": number,
        "Size": size
    }

    # Add to session state (not persisted to CSV)
    new_row_df = pd.DataFrame([row])
    st.session_state.data_df = pd.concat([st.session_state.data_df, new_row_df], ignore_index=True)

    st.success("Data saved for current session!")

# Display current data
st.header("📊 Current Data")

# Show all data - merge uploaded data with session state data
display_df = st.session_state.data_df.copy()
if st.session_state.uploaded_data_df is not None:
    # Add uploaded data to existing session data (don't overwrite)
    display_df = pd.concat([display_df, st.session_state.uploaded_data_df], ignore_index=True)

if not display_df.empty:
    # Make Cat Breed column editable in the dataframe
    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        column_config={
            "Cat Breed": st.column_config.SelectboxColumn(
                "Cat Breed",
                help="Cat breed (editable)",
                options=CAT_CLASSES,
                required=False
            )
        }
    )
    
    # Update session state with edited data
    st.session_state.data_df = edited_df.copy()
else:
    st.info("No data in current session. Upload a CSV file or enter new data above.")

# Download button for current session data (includes both entered and uploaded data)
if not display_df.empty:
    st.header("💾 Download Data")
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV File",
        data=csv,
        file_name="cat_data.csv",
        mime="text/csv"
    )
