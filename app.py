#before start to write flask install the flsk in
#Anaconda prompt:Admin  (pip install flask) then start the coding ..

from flask import Flask, request, render_template, jsonify
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import os

app = Flask(__name__)

model = load_model("fish_disease_model.h5")

disease_info = {
    'Healthy Fish': {
        'treatment': 'Your fish is healthy! Keep maintaining clean water.',
        'cause': 'No disease detected.',
        'solution': 'Continue regular feeding and water changes.'
    },
    'Bacterial diseases - Aeromoniasis': {
        'treatment': 'Use antibiotics like Oxytetracycline in water.',
        'cause': 'Caused by Aeromonas bacteria in dirty water.',
        'solution': 'Isolate fish, clean tank, add aquarium salt.'
    },
    'Bacterial gill disease': {
        'treatment': 'Use potassium permanganate bath treatment.',
        'cause': 'Caused by bacteria attacking gill tissue.',
        'solution': 'Improve water oxygen levels and cleanliness.'
    },
    'Bacterial Red disease': {
        'treatment': 'Use antibiotic treatment in food or water.',
        'cause': 'Bacterial infection causing red spots.',
        'solution': 'Quarantine fish and treat with antibiotics.'
    },
    'Fungal diseases Saprolegniasis': {
        'treatment': 'Use antifungal medicine like Malachite Green.',
        'cause': 'Fungal infection from poor water quality.',
        'solution': 'Clean tank thoroughly and treat with antifungal.'
    },
    'Parasitic diseases': {
        'treatment': 'Use antiparasitic treatment like Formalin bath.',
        'cause': 'Parasites attacking fish skin or gills.',
        'solution': 'Quarantine and treat with antiparasitic medicine.'
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
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

    if disease == 'Not a fish':
        return jsonify({
            'error': '⚠️ This is not a valid fish image. Please upload a clear fish image!'
        })

    info = disease_info[disease]

    return jsonify({
        'disease': disease,
        'confidence': confidence,
        'treatment': info['treatment'],
        'cause': info['cause'],
        'solution': info['solution']
    })

if __name__ == '__main__':
    app.run(debug=True)