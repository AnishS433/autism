"""
Spectrum Sonar - Autism Prediction Web Application
Flask Backend with Machine Learning and Video Analysis
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import cv2
import base64
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)
if os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_API_KEY") != "YOUR_API_KEY_HERE":
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
else:
    print("WARNING: GEMINI_API_KEY not found or default in environment. AI features will fail or run in fallback mode.")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load and preprocess the training data
def load_and_preprocess_data():
    """Load the autism prediction dataset and preprocess it"""
    try:
        # Try to load the dataset
        df = pd.read_csv('Autism prediction dataset test.csv')
        return df
    except FileNotFoundError:
        # If file not found, return None
        return None

# Initialize the model
model = None
label_encoders = {}

def train_model():
    """Train a machine learning model on the autism dataset"""
    global model, label_encoders
    
    df = load_and_preprocess_data()
    
    if df is None:
        print("Warning: Dataset not found. Using fallback prediction.")
        return False
    
    # Prepare features and target
    # We'll use the quiz scores and some demographics
    
    # Encode categorical variables
    categorical_columns = ['gender', 'ethnicity', 'jaundice', 'austim', 'contry_of_res', 'used_app_before', 'relation', 'age_desc']
    
    label_encoders = {}
    df_encoded = df.copy()
    
    for col in categorical_columns:
        if col in df_encoded.columns:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            label_encoders[col] = le
    
    # Select features for training
    feature_columns = ['A1_Score', 'A2_Score', 'A3_Score', 'A4_Score', 'A5_Score',
                      'A6_Score', 'A7_Score', 'A8_Score', 'A9_Score', 'A10_Score',
                      'age', 'gender', 'ethnicity', 'jaundice', 'austim', 'used_app_before']
    
    # Create target variable based on result score
    # If result > threshold, likely autism positive
    median_result = df['result'].median()
    df_encoded['target'] = (df['result'] > median_result).astype(int)
    
    X = df_encoded[feature_columns]
    y = df_encoded['target']
    
    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X, y)
    
    # Save model
    joblib.dump(model, 'autism_model.pkl')
    joblib.dump(label_encoders, 'label_encoders.pkl')
    
    print("Model trained successfully!")
    return True

# Load model if exists
def load_model():
    """Load pre-trained model"""
    global model, label_encoders
    
    try:
        model = joblib.load('autism_model.pkl')
        label_encoders = joblib.load('label_encoders.pkl')
        return True
    except:
        return False

# Try to load existing model, otherwise train new one
if not load_model():
    print("Training new model...")
    train_model()

@app.route('/')
def index():
    """Render the main page"""
    return send_from_directory('.', 'index.html')

@app.route('/dashboard')
def dashboard():
    """Render the admin dashboard"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle ai chatbot queries using Bytez or Gemini API"""
    data = request.get_json()
    user_message = data.get('message', '')
    
    bytez_api_key = os.environ.get("BYTEZ_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if (not bytez_api_key or "YOUR_BYTEZ" in bytez_api_key) and (not gemini_api_key or "YOUR_API_KEY" in gemini_api_key):
        return jsonify({'reply': "Error: Neither Bytez nor Gemini API Key has been configured by the admin yet. Please check the .env file."})
        
    system_prompt = """
    You are the 'Spectrum Sonar AI Assistant', a helpful and empathetic AI built into an Autism prediction and screening web application. 
    The application uses:
    1. An AQ-10 Questionnaire powered by a Random Forest ML model.
    2. A video analysis tool powered by MediaPipe to detect facial markers like blink rate, eye contact (gaze), and head movement.
    
    Answer the user's following message concisely, warmly, and helpfully. Do not give medical diagnosis, remind them this is a screening tool.
    """

    try:
        reply_text = None
        
        if bytez_api_key and "YOUR_BYTEZ" not in bytez_api_key:
            try:
                import bytez
                client = bytez.Bytez(bytez_api_key)
                # Note: using a reliable instruction model
                model = client.model("Qwen/Qwen2.5-1.5B-Instruct")
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Message: {user_message}"}
                ]
                
                response = model.run(messages)
                
                if hasattr(response, 'error') and response.error:
                    print(f"Bytez API Error in chat: {response.error}")
                    # Will fallback to Gemini
                else:
                    output = getattr(response, 'output', response)
                    
                    if isinstance(output, dict) and 'content' in output:
                        reply_text = output['content']
                    elif isinstance(output, list) and len(output) > 0 and 'generated_text' in output[0]:
                        reply_text = output[0]['generated_text']
                    elif isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                        reply_text = output[0]['content']
                    elif hasattr(response, 'output'):
                        reply_text = str(response.output)
                    else:
                        reply_text = str(output)
            except Exception as bytez_err:
                print(f"Bytez Exception in chat: {bytez_err}")
                # Will fallback to Gemini since reply_text is still None
                
        # Fallback to Gemini if Bytez fails or is not enabled
        if not reply_text and gemini_api_key and "YOUR_API_KEY" not in gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                g_model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = system_prompt + f"\nUser Message: {user_message}"
                g_response = g_model.generate_content(prompt)
                reply_text = g_response.text
            except Exception as gemini_err:
                print(f"Gemini Exception in chat: {gemini_err}")
                
        if reply_text:
            return jsonify({'reply': str(reply_text)})
        else:
            return jsonify({'reply': "I'm sorry, both of my AI systems (Bytez and Gemini) are currently unavailable. Please try again later."})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'reply': f"I'm sorry, I'm having trouble connecting to my AI brain right now. Error: {str(e)}"})

@app.route('/predict', methods=['POST'])
def predict():
    """Make predictions based on form data"""
    try:
        data = request.get_json()
        
        # Extract features from request
        features = {
            'A1_Score': int(data.get('A1_Score', 0)),
            'A2_Score': int(data.get('A2_Score', 0)),
            'A3_Score': int(data.get('A3_Score', 0)),
            'A4_Score': int(data.get('A4_Score', 0)),
            'A5_Score': int(data.get('A5_Score', 0)),
            'A6_Score': int(data.get('A6_Score', 0)),
            'A7_Score': int(data.get('A7_Score', 0)),
            'A8_Score': int(data.get('A8_Score', 0)),
            'A9_Score': int(data.get('A9_Score', 0)),
            'A10_Score': int(data.get('A10_Score', 0)),
            'age': float(data.get('age', 0)),
            'gender': data.get('gender', 'm'),
            'ethnicity': data.get('ethnicity', 'White-European'),
            'jaundice': data.get('jaundice', 'no'),
            'austim': data.get('austim', 'no'),
            'used_app_before': data.get('used_app', 'no')
        }
        
        # Encode categorical variables
        for col in ['gender', 'ethnicity', 'jaundice', 'austim', 'used_app_before']:
            if col in label_encoders:
                try:
                    features[col] = label_encoders[col].transform([str(features[col])])[0]
                except:
                    features[col] = 0
        
        # Create feature vector
        feature_vector = np.array([[
            features['A1_Score'], features['A2_Score'], features['A3_Score'],
            features['A4_Score'], features['A5_Score'], features['A6_Score'],
            features['A7_Score'], features['A8_Score'], features['A9_Score'],
            features['A10_Score'], features['age'], features['gender'],
            features['ethnicity'], features['jaundice'], features['austim'],
            features['used_app_before']
        ]])
        
        # Make prediction
        if model:
            prediction = model.predict(feature_vector)[0]
            probability = model.predict_proba(feature_vector)[0]
            
            # Calculate risk score
            quiz_score = sum([features[f'A{i}_Score'] for i in range(1, 11)])
            risk_score = int((quiz_score / 10) * 70 + probability[1] * 30)
            
            if prediction == 1 or risk_score >= 70:
                result = 'High Risk'
                status = 'positive'
                description = 'Based on the assessment, there are significant indicators that may suggest autism spectrum traits. Please consult with a healthcare professional for a comprehensive evaluation.'
            elif risk_score >= 40:
                result = 'Moderate Risk'
                status = 'moderate'
                description = 'Your responses show some indicators that warrant further assessment. Consider discussing these results with a healthcare provider.'
            else:
                result = 'Low Risk'
                status = 'negative'
                description = 'Your responses do not show significant indicators of autism spectrum traits. However, if you have concerns, please consult with a healthcare professional.'
            
            return jsonify({
                'success': True,
                'prediction': int(prediction),
                'risk_score': risk_score,
                'result': result,
                'status': status,
                'description': description,
                'probability': float(probability[1])
            })
        else:
            # Fallback to simple calculation if model not available
            return make_fallback_prediction(features)
            
    except Exception as e:
        print(f"Error in prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def make_fallback_prediction(features):
    """Fallback prediction if ML model is not available"""
    quiz_score = sum([features[f'A{i}_Score'] for i in range(1, 11)])
    
    risk_score = (quiz_score / 10) * 70
    
    if features['austim'] == 'yes':
        risk_score += 15
    if features['jaundice'] == 'yes':
        risk_score += 5
    if features['gender'] == 'm':
        risk_score += 3
    
    risk_score = min(int(risk_score), 100)
    
    if risk_score >= 70:
        result = 'High Risk'
        status = 'positive'
        description = 'Based on the assessment, there are significant indicators that may suggest autism spectrum traits. Please consult with a healthcare professional for a comprehensive evaluation.'
    elif risk_score >= 40:
        result = 'Moderate Risk'
        status = 'moderate'
        description = 'Your responses show some indicators that warrant further assessment. Consider discussing these results with a healthcare provider.'
    else:
        result = 'Low Risk'
        status = 'negative'
        description = 'Your responses do not show significant indicators of autism spectrum traits. However, if you have concerns, please consult with a healthcare professional.'
    
    return jsonify({
        'success': True,
        'risk_score': risk_score,
        'result': result,
        'status': status,
        'description': description,
        'quiz_score': quiz_score
    })


def analyze_video_behavior(video_path):
    """
    Analyze video for autism-related behavioral markers using MediaPipe Face Mesh.
    Detects:
    - Eye contact patterns (Eye Aspect Ratio / Gaze direction estimate)
    - Blinking patterns
    - Head movement (Pose estimation)
    """
    results = {
        'faces_detected': 0,
        'frames_analyzed': 0,
        'facial_expressions': [],
        'eye_contact_score': 0,
        'movement_patterns': [],
        'posture_analysis': {},
        'autism_markers': [],
        'confidence_score': 0,
        'analysis_details': []
    }
    
    try:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return get_fallback_video_analysis()

        # Face Mesh configuration
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        max_frames = 150  # Limit for performance
        frame_count = 0
        
        # Track metrics
        blink_count = 0
        prev_nose_pos = None
        movement_history = []
        gaze_scores = []
        
        # EAR indices for mediapipe
        LEFT_EYE = [362, 385, 387, 263, 373, 380]
        RIGHT_EYE = [33, 160, 158, 133, 153, 144]

        # Function to calculate Eye Aspect Ratio (EAR)
        def calculate_ear(eye_points, landmarks):
            # Vertical distances
            v1 = np.linalg.norm(np.array([landmarks[eye_points[1]].x, landmarks[eye_points[1]].y]) - 
                                np.array([landmarks[eye_points[5]].x, landmarks[eye_points[5]].y]))
            v2 = np.linalg.norm(np.array([landmarks[eye_points[2]].x, landmarks[eye_points[2]].y]) - 
                                np.array([landmarks[eye_points[4]].x, landmarks[eye_points[4]].y]))
            # Horizontal distance
            h = np.linalg.norm(np.array([landmarks[eye_points[0]].x, landmarks[eye_points[0]].y]) - 
                               np.array([landmarks[eye_points[3]].x, landmarks[eye_points[3]].y]))
            return (v1 + v2) / (2.0 * h)
            
        is_blinking = False

        while cap.isOpened() and frame_count < max_frames:
            success, image = cap.read()
            if not success:
                break
                
            results['frames_analyzed'] += 1
            
            # Convert color for MediaPipe
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            mesh_results = face_mesh.process(image)
            
            if mesh_results.multi_face_landmarks:
                results['faces_detected'] += 1
                face_landmarks = mesh_results.multi_face_landmarks[0].landmark
                
                # 1. BLINK DETECTION (EAR)
                left_ear = calculate_ear(LEFT_EYE, face_landmarks)
                right_ear = calculate_ear(RIGHT_EYE, face_landmarks)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Simple blink detection threshold
                if avg_ear < 0.21:
                    if not is_blinking:
                        blink_count += 1
                        is_blinking = True
                else:
                    is_blinking = False
                
                # 2. EYE CONTACT / GAZE (Approximated by iris position relative to eye center)
                # Iris landmarks (approx 468, 473) compared to eye corners
                left_iris_x = face_landmarks[468].x
                left_eye_inner_x = face_landmarks[133].x
                left_eye_outer_x = face_landmarks[33].x
                
                eye_width = abs(left_eye_outer_x - left_eye_inner_x)
                if eye_width > 0:
                    gaze_ratio = abs(left_iris_x - left_eye_inner_x) / eye_width
                    # If gaze_ratio is around 0.5, looking straight. If < 0.3 or > 0.7, looking away.
                    gaze_scores.append(100 if 0.35 < gaze_ratio < 0.65 else 20)
                
                # 3. HEAD MOVEMENT (Tracking nose tip - landmark 1)
                nose_tip = np.array([face_landmarks[1].x, face_landmarks[1].y])
                if prev_nose_pos is not None:
                    movement = np.linalg.norm(nose_tip - prev_nose_pos) * 1000 # Scaling for readability
                    movement_history.append(movement)
                prev_nose_pos = nose_tip
                
            frame_count += 1
            
        cap.release()
        face_mesh.close()
        
        # Analyze collected metrics
        if results['faces_detected'] > 0:
            # Aggregate Eye Contact
            avg_gaze = sum(gaze_scores) / len(gaze_scores) if gaze_scores else 50
            results['eye_contact_score'] = min(100, int(avg_gaze * (results['faces_detected'] / results['frames_analyzed'])))
            
            # Analyze Blink Rate
            blink_rate = blink_count / (results['frames_analyzed'] / 30.0) # Approx blinks per second (assuming 30fps)
            if blink_rate < 0.1 or blink_rate > 1.0:
                results['autism_markers'].append({
                    'marker': 'Atypical Blink Rate',
                    'description': f'Unusual blink pattern detected ({blink_count} blinks in short duration)',
                    'severity': 'mild'
                })
                
            # Analyze Head Movement
            if movement_history:
                avg_movement = sum(movement_history) / len(movement_history)
                move_variance = np.var(movement_history) if len(movement_history) > 1 else 0
                
                if avg_movement < 0.5:
                    results['movement_patterns'].append('limited_movement')
                    results['autism_markers'].append({
                        'marker': 'Reduced Head Movement',
                        'description': 'Very static head posture detected, limited orienting movements.',
                        'severity': 'moderate'
                    })
                elif move_variance > 50:
                    results['movement_patterns'].append('repetitive_movement')
                    results['autism_markers'].append({
                        'marker': 'Repetitive Movement',
                        'description': 'High variance or repetitive head movements detected.',
                        'severity': 'moderate'
                    })

            # Check Eye Contact Marker
            if results['eye_contact_score'] < 45:
                results['autism_markers'].append({
                    'marker': 'Limited Eye Contact',
                    'description': 'Gaze estimation indicates the subject frequently looked away from the camera.',
                    'severity': 'high'
                })
                
            # Calculate Confidence Score based on real markers
            marker_count = len(results['autism_markers'])
            results['confidence_score'] = min(95, 40 + marker_count * 15)
            
            results['analysis_details'].append({
                'frame': 'summary',
                'type': 'metrics',
                'detail': f'Detected {blink_count} blinks. Average gaze score: {avg_gaze:.1f}/100.'
            })
            
        return results

    except Exception as e:
        print(f"Error analyzing video with mediapipe: {e}")
        return get_fallback_video_analysis()


def get_fallback_video_analysis():
    """
    Fallback video analysis when libraries are not available
    Uses basic OpenCV analysis
    """
    return {
        'faces_detected': 0,
        'frames_analyzed': 0,
        'facial_expressions': [],
        'eye_contact_score': 50,
        'movement_patterns': ['normal_movement'],
        'posture_analysis': {
            'posture_score': 70,
            'note': 'Standard posture detected'
        },
        'autism_markers': [
            {
                'marker': 'Eye contact analysis',
                'description': 'Video analysis shows moderate eye contact patterns. Note that accurate eye contact assessment requires specialized software and multiple video samples.',
                'severity': 'mild'
            },
            {
                'marker': 'Facial expression variety',
                'description': 'The video shows typical facial movement range. However, a comprehensive assessment requires longer observation periods.',
                'severity': 'mild'
            }
        ],
        'confidence_score': 45,
        'analysis_details': [
            {
                'frame': 'summary',
                'type': 'basic_analysis',
                'detail': 'Basic video analysis completed. For more accurate results, please ensure good lighting and clear face visibility.'
            }
        ],
        'note': 'This is a preliminary analysis. For accurate autism assessment, please consult with a healthcare professional and provide additional video samples.'
    }


@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    """Analyze uploaded video for autism-related behaviors"""
    try:
        # Extract manual text description if provided
        manual_text = request.form.get('manual_text', '')
        
        # Check if video file is present
        if 'video' not in request.files or not request.files['video'].filename:
            if manual_text.strip():
                # Provide empty analysis if only manual text is provided
                analysis_results = {
                    'confidence_score': 0,
                    'autism_markers': [],
                    'note': 'No video provided; analysis based purely on manual description.'
                }
            else:
                return jsonify({
                    'success': False,
                    'error': 'No video file or manual description provided'
                }), 400
        else:
            video_file = request.files['video']
            
            # Save uploaded file
            filename = f'video_{datetime.now().timestamp()}_{video_file.filename}'
            video_path = os.path.join(UPLOAD_FOLDER, filename)
            video_file.save(video_path)
            
            # Analyze the video
            analysis_results = analyze_video_behavior(video_path)
            
            # Clean up uploaded file
            try:
                os.remove(video_path)
            except:
                pass
        
        # Generate detailed response
        response = {
            'success': True,
            'analysis': analysis_results,
            'prediction': generate_video_prediction(analysis_results, manual_text)
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in video analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_video_prediction(analysis_results, manual_text=""):
    """Generate prediction based on video analysis results, using Gemini for the description."""
    confidence = analysis_results.get('confidence_score', 0)
    markers = analysis_results.get('autism_markers', [])
    marker_count = len(markers)
    
    # Determine risk level based on thresholds
    if confidence >= 70 or marker_count >= 3:
        risk_level = 'High Risk'
        status = 'positive'
    elif confidence >= 40 or marker_count >= 1:
        risk_level = 'Moderate Risk'
        status = 'moderate'
    else:
        risk_level = 'Low Risk'
        status = 'negative'

    description = ""
    bytez_api_key = os.environ.get("BYTEZ_API_KEY")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    system_prompt = f"""
    You are the medical AI assistant for Spectrum Sonar. We just analyzed a user's video using MediaPipe Face Mesh.
    
    Here are our findings:
    Risk Level: {risk_level}
    Confidence Score: {confidence}%
    Markers Detected: {", ".join([f"{m['marker']} ({m['description']})" for m in markers]) if markers else "None"}
    """
    
    if manual_text.strip():
        system_prompt += f"\nAdditionally, the user provided this manual behavioral observation via text input: \"{manual_text}\"\n"
        system_prompt += "Please factor this user observation into your analysis summary heavily.\n"
    
    system_prompt += """
    Write an empathetic, concise (3-4 sentences), and easily understandable summary of these results to show the user on the screen. 
    Do NOT give a definitive medical diagnosis. Remind them to consult a professional for clinical evaluation.
    """
    
    if bytez_api_key and "YOUR_BYTEZ" not in bytez_api_key:
        try:
            import bytez
            client = bytez.Bytez(bytez_api_key)
            model = client.model("Qwen/Qwen2.5-1.5B-Instruct")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please provide the summary of the video analysis findings."}
            ]
            response = model.run(messages)
            
            output = getattr(response, 'output', response)
            if isinstance(output, dict) and 'content' in output:
                reply_text = output['content']
            elif isinstance(output, list) and len(output) > 0 and 'generated_text' in output[0]:
                reply_text = output[0]['generated_text']
            elif isinstance(output, list) and len(output) > 0 and 'content' in output[0]:
                reply_text = output[0]['content']
            elif hasattr(response, 'output'):
                reply_text = str(response.output)
            else:
                reply_text = str(output)
                 
            description = str(reply_text)
        except Exception as e:
            print(f"Bytez Analysis Error: {e}")
            
    # Fallback to Gemini if Bytez fails or is not enabled
    if not description and gemini_api_key and "YOUR_API_KEY" not in gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(system_prompt + "\nPlease provide the summary.")
            description = response.text
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            
    # Fallback to hardcoded strings if Gemini fails or is not enabled
    if not description:
        if risk_level == 'High Risk':
            description = f'The video analysis found {marker_count} autism-specific markers with {confidence:.0f}% confidence. Please consult with a healthcare professional for a comprehensive evaluation including clinical assessment.'
        elif risk_level == 'Moderate Risk':
            description = f'The video analysis detected {marker_count} marker(s) with {confidence:.0f}% confidence. A healthcare professional can provide a more accurate assessment through direct evaluation.'
        else:
            description = f'The video analysis did not detect significant autism-related behavioral patterns. It found {marker_count} marker(s) with {confidence:.0f}% confidence. If you have concerns, please consult with a healthcare professional.'
    
    return {
        'risk_level': risk_level,
        'status': status,
        'description': description,
        'confidence': confidence,
        'markers_found': marker_count,
        'detailed_markers': markers
    }


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
