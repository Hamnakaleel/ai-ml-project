#before start to write flask install the flsk in
#Anaconda prompt:Admin  (pip install flask) then start the coding ..

from flask import Flask, request, render_template, jsonify, send_file
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import google.generativeai as genai
import os
import io
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Load environment variables from .env file
load_dotenv()
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# -------------------------------------------------
# Load Environment Variables
# -------------------------------------------------
load_dotenv()  # Load from .env file

# -------------------------------------------------
# Flask App
# -------------------------------------------------
app = Flask(__name__)

# -------------------------------------------------
# Gemini API Configuration
# -------------------------------------------------
# API key is loaded from .env file
api_key = os.getenv("GEMINI_API_KEY")
print(api_key)

if api_key:
    genai.configure(api_key=api_key)
    # Try gemini-pro first (stable), fallback to gemini-1.5-flash
    try:
        gemini_model = genai.GenerativeModel("gemma-4-26b-a4b-it")
        print("✅ Gemini API configured with gemini-pro model")
    except Exception as e:
        print(f"⚠️  Failed to load gemini-pro: {e}")
        try:
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            print("✅ Gemini API configured with gemini-1.5-flash model")
        except Exception as e2:
            print(f"⚠️  Failed to load gemini-1.5-flash: {e2}")
            gemini_model = None
else:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")
    print("   Chat feature will not work until API key is added")
    gemini_model = None

# -------------------------------------------------
# Load ML Model
# -------------------------------------------------
model = load_model("fish_disease_model.h5")

# -------------------------------------------------
# Disease Information
# -------------------------------------------------
disease_info = {
    'Healthy Fish': {
        'cause': 'No disease detected.',
        'symptoms': 'Bright body color, smooth skin, active swimming.',
        'treatment': 'No treatment required.',
        'prevention': 'Maintain clean water and proper feeding.',
        'organ': 'N/A',
        'solution': 'Keep water clean and balanced.'
    },
    'Bacterial diseases - Aeromoniasis': {
        'cause': 'Poor water quality and stress.',
        'symptoms': 'Red ulcers, swollen abdomen, fin rot.',
        'treatment': 'Use antibiotics and isolate fish.',
        'prevention': 'Clean tank regularly.',
        'organ': 'Skin, fins, internal organs',
        'solution': 'Quarantine and treat with antibiotics.'
    },
    'Bacterial gill disease': {
        'cause': 'High ammonia and low oxygen.',
        'symptoms': 'Swollen gills, breathing difficulty.',
        'treatment': 'Improve water quality and oxygen.',
        'prevention': 'Avoid overcrowding.',
        'organ': 'Gills',
        'solution': 'Increase oxygen and clean tank.'
    },
    'Bacterial Red disease': {
        'cause': 'Bacterial infection through wounds.',
        'symptoms': 'Red patches and bleeding fins.',
        'treatment': 'Antibiotic treatment.',
        'prevention': 'Good hygiene and clean water.',
        'organ': 'Skin and fins',
        'solution': 'Isolate fish and apply antibiotics.'
    },
    'Fungal diseases Saprolegniasis': {
        'cause': 'Injuries and poor water quality.',
        'symptoms': 'White cotton-like patches.',
        'treatment': 'Antifungal medicine.',
        'prevention': 'Remove dead fish quickly.',
        'organ': 'Skin and gills',
        'solution': 'Clean tank and use antifungal.'
    },
    'Parasitic diseases': {
        'cause': 'Parasites in contaminated water.',
        'symptoms': 'White spots and scratching.',
        'treatment': 'Antiparasitic medicine.',
        'prevention': 'Quarantine new fish.',
        'organ': 'Skin and gills',
        'solution': 'Quarantine and medicate.'
    }
}

class_names = {
    0: 'Bacterial Red disease',
    1: 'Bacterial diseases - Aeromoniasis',
    2: 'Bacterial gill disease',
    3: 'Fungal diseases Saprolegniasis',
    4: 'Healthy Fish',
    5: 'Not a fish',
    6: 'Parasitic diseases'
}

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------------------------------
# Image Prediction
# -------------------------------------------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    static_folder = os.path.join(app.root_path, 'static')
    os.makedirs(static_folder, exist_ok=True)

    img_path = os.path.join(static_folder, 'uploaded.jpg')
    file.save(img_path)

    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    prediction = model.predict(img_array)
    class_idx = int(np.argmax(prediction))
    confidence = round(float(np.max(prediction)) * 100, 2)
    disease = class_names[class_idx]

    if confidence < 60.0:
        return jsonify({
            'error': '⚠️ Low confidence in prediction. Please upload a clearer image of the fish for better results!'
        })

    if disease == 'Not a fish':
        return jsonify({
            'error': '⚠️ This is not a valid fish image. Please upload a clear fish image!'
        })

    info = disease_info[disease]

    return jsonify({
        'disease': disease,
        'confidence': confidence,
        'cause': info['cause'],
        'symptoms': info['symptoms'],
        'treatment': info['treatment'],
        'prevention': info['prevention'],
        'organ': info['organ'],
        'solution': info['solution']
    })

# -------------------------------------------------
# PDF Report
# -------------------------------------------------
@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.get_json()
    disease = data.get('disease', '')
    confidence = data.get('confidence', '')
    info = disease_info.get(disease, {})

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#0077b6')
    )

    story.append(Paragraph("Fish Disease Detection Report", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Disease:</b> {disease}", styles['Normal']))
    story.append(Paragraph(f"<b>Confidence:</b> {confidence}%", styles['Normal']))
    story.append(Spacer(1, 15))

    table_data = [
        ['Field', 'Details'],
        ['Organ', info.get('organ', 'N/A')],
        ['Cause', info.get('cause', 'N/A')],
        ['Symptoms', info.get('symptoms', 'N/A')],
        ['Treatment', info.get('treatment', 'N/A')],
        ['Prevention', info.get('prevention', 'N/A')],
    ]

    table = Table(table_data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0077b6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(table)
    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="fish_disease_report.pdf",
        mimetype="application/pdf"
    )

# -------------------------------------------------
# Gemini Chatbot
# -------------------------------------------------
@app.route('/chat', methods=['POST'])
def chat():
    if not gemini_model:
        return jsonify({'reply': 'Chat service is currently unavailable. Please add GEMINI_API_KEY to .env file.'})
    
    data = request.get_json()
    user_message = data.get('message', '')
    language = data.get('language', 'english')
    
    # System prompts in each language
    system_prompts = {
        'english': """You are a fish disease expert assistant. 

Answer questions about fish diseases, treatments, and prevention.
Use markdown formatting (headers, bold, lists).
Be concise and professional.
If unsure, recommend consulting a professional.""",
        
        'tamil': """நீங்கள் ஒரு மீன் நோய் நிபுணர் உதவியாளர்.

மீன் நோய்கள், சிகிச்சைகள் மற்றும் தடுப்பு முறைகள் பற்றிய கேள்விகளுக்கு பதிலளிக்கவும்.
மார்க்டவுன் வடிவமைப்பைப் பயன்படுத்தவும் (தலைப்புகள், தடிப்பு, பட்டியல்).
சுருக்கமாகவும் தொழிலாதாரமாகவும் இருங்கள்.
உறுதியற்றால், ஒரு நிபுணரை அணுக பரிந்துரை செய்யுங்கள்.""",
        
        'sinhala': """ඔබ මත්ස්‍ය රෝග විශේෂඥ සහායකයෙකි.

මත්ස්‍ය රෝග, ප්‍රතිකාර සහ වැළැක්වීමේ ක්‍රම පිළිබඳ ප්‍රශ්නවලට පිළිතුරු දෙන්න.
Markdown ආකෘතිය භාවිතා කරන්න (මාතෘකා, තරමින් කුඩා, ලැයිස්තු).
සංක්ෂිප්ත සහ වෘත්තීය වන්න.
අවිනිශ්චිතව සිටින්නේ නම්, විශේෂඥයෙකු අවලඝන සඳහා පෙන්වා දෙන්න.""",

        'hindi': """आप एक मछली रोग विशेषज्ञ सहायक हैं।

मछली के रोगों, उपचारों और रोकथाम के बारे में सवालों के जवाब दें।
Markdown फॉर्मेटिंग का उपयोग करें (शीर्षक, बोल्ड, सूचियां)।
संक्षिप्त और पेशेवर रहें।
यदि अनिश्चित हैं, तो एक पेशेवर से परामर्श करने की सिफारिश करें।"""
    }
    
    system_prompt = system_prompts.get(language, system_prompts['english'])
    
    try:
        prompt = f"""{system_prompt}

User question: {user_message}"""
        response = gemini_model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        reply = f"Sorry, I encountered an error: {str(e)}"
    
    return jsonify({'reply': reply})

# -------------------------------------------------
# Run App
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)