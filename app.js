// Spectrum Sonar - Autism Prediction Web Application
// JavaScript for handling form submissions, predictions, and video analysis

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('autism-form');
    const resultsSection = document.getElementById('results');
    const quizSection = document.getElementById('quiz');

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form submission handler
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const submitBtn = form.querySelector('.btn-submit');
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;

            try {
                // Collect form data
                const formData = collectFormData();

                // Make prediction (using local calculation since we don't have a backend)
                const prediction = await makePrediction(formData);

                // Display results
                displayResults(prediction, formData);

                // Scroll to results
                resultsSection.style.display = 'block';
                quizSection.style.display = 'none';
                resultsSection.scrollIntoView({ behavior: 'smooth' });

            } catch (error) {
                console.error('Error making prediction:', error);
                alert('An error occurred while making the prediction. Please try again.');
            } finally {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        });
    }

    // Initialize video analysis functionality
    initVideoAnalysis();
});

// Collect all form data
function collectFormData() {
    const data = {
        // Demographics
        age: parseFloat(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        ethnicity: document.getElementById('ethnicity').value,
        country: document.getElementById('country').value,

        // Medical history
        jaundice: document.getElementById('jaundice').value,
        austim: document.getElementById('austim').value,

        // Relation and app usage
        relation: document.getElementById('relation').value,
        used_app: document.getElementById('used_app').value,

        // Quiz scores (AQ-10)
        A1_Score: parseInt(document.querySelector('input[name="A1_Score"]:checked')?.value || 0),
        A2_Score: parseInt(document.querySelector('input[name="A2_Score"]:checked')?.value || 0),
        A3_Score: parseInt(document.querySelector('input[name="A3_Score"]:checked')?.value || 0),
        A4_Score: parseInt(document.querySelector('input[name="A4_Score"]:checked')?.value || 0),
        A5_Score: parseInt(document.querySelector('input[name="A5_Score"]:checked')?.value || 0),
        A6_Score: parseInt(document.querySelector('input[name="A6_Score"]:checked')?.value || 0),
        A7_Score: parseInt(document.querySelector('input[name="A7_Score"]:checked')?.value || 0),
        A8_Score: parseInt(document.querySelector('input[name="A8_Score"]:checked')?.value || 0),
        A9_Score: parseInt(document.querySelector('input[name="A9_Score"]:checked')?.value || 0),
        A10_Score: parseInt(document.querySelector('input[name="A10_Score"]:checked')?.value || 0)
    };

    // Calculate total quiz score
    data.totalScore = data.A1_Score + data.A2_Score + data.A3_Score + data.A4_Score +
        data.A5_Score + data.A6_Score + data.A7_Score + data.A8_Score +
        data.A9_Score + data.A10_Score;

    return data;
}

async function makePrediction(data) {
    try {
        const response = await fetch('http://127.0.0.1:5001/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return {
            score: result.confidence ? Math.round(result.confidence * 100) : (result.result === 'High Risk' ? 85 : 15),
            result: result.result,
            status: result.status,
            description: result.description || (result.result === 'High Risk' ? 'Based on the ML model, there are significant indicators.' : 'Based on the ML model, low risk.'),
            totalQuizScore: data.totalScore
        };
    } catch (error) {
        console.error('Prediction API Error, falling back to local calculation:', error);
        // Fallback calculation
        let predictionScore = (data.totalScore / 10) * 70;
        if (data.austim === 'yes') predictionScore += 15;
        if (data.jaundice === 'yes') predictionScore += 5;

        const normalizedScore = Math.min(Math.round(predictionScore), 100);
        let result = normalizedScore >= 70 ? 'High Risk' : (normalizedScore >= 40 ? 'Moderate Risk' : 'Low Risk');
        let status = normalizedScore >= 70 ? 'positive' : (normalizedScore >= 40 ? 'moderate' : 'negative');
        let description = 'Uses local fallback estimation. Could not reach server.';

        return { score: normalizedScore, result, status, description, totalQuizScore: data.totalScore };
    }
}

// Display the prediction results
function displayResults(prediction, formData) {
    const resultIcon = document.getElementById('result-icon');
    const resultStatus = document.getElementById('result-status');
    const resultScore = document.getElementById('result-score');
    const resultDescription = document.getElementById('result-description');
    const summaryContent = document.getElementById('summary-content');

    // Set result icon
    if (prediction.status === 'positive') {
        resultIcon.textContent = '⚠️';
    } else if (prediction.status === 'moderate') {
        resultIcon.textContent = '🤔';
    } else {
        resultIcon.textContent = '✅';
    }

    // Set result status
    resultStatus.textContent = prediction.result;
    resultStatus.className = 'result-status ' + prediction.status;

    // Set result score
    resultScore.textContent = prediction.score + '%';

    // Set description
    resultDescription.textContent = prediction.description;

    // Generate summary
    let summaryHTML = `
        <div class="summary-item">
            <span class="summary-label">Age</span>
            <span class="summary-value">${formData.age} years</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">Gender</span>
            <span class="summary-value">${formData.gender === 'm' ? 'Male' : 'Female'}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">Ethnicity</span>
            <span class="summary-value">${formData.ethnicity}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">Country</span>
            <span class="summary-value">${formData.country}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">Family History of Autism</span>
            <span class="summary-value">${formData.austim === 'yes' ? 'Yes' : 'No'}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">History of Jaundice</span>
            <span class="summary-value">${formData.jaundice === 'yes' ? 'Yes' : 'No'}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">Quiz Score</span>
            <span class="summary-value">${formData.totalScore} / 10</span>
        </div>
    `;

    // Add individual question responses
    summaryHTML += '<div class="summary-item" style="margin-top: 1rem;"><span class="summary-label" style="font-weight: 600;">Question Responses</span></div>';

    const questions = [
        'Notices small sounds',
        'Concentrates on whole picture',
        'Does multiple things at once',
        'Switches back quickly',
        'Reads between the lines',
        'Notices boredom',
        'Understands characters',
        'Collects information',
        'Reads facial expressions',
        'Understands intentions'
    ];

    for (let i = 1; i <= 10; i++) {
        const score = formData['A' + i + '_Score'];
        summaryHTML += `
            <div class="summary-item">
                <span class="summary-label">Q${i}: ${questions[i - 1]}</span>
                <span class="summary-value">${score === 1 ? 'Yes' : 'No'}</span>
            </div>
        `;
    }

    summaryContent.innerHTML = summaryHTML;
}

// Reset form and go back to quiz
function resetForm() {
    const form = document.getElementById('autism-form');
    const resultsSection = document.getElementById('results');
    const quizSection = document.getElementById('quiz');

    // Reset form
    form.reset();

    // Hide results and show quiz
    resultsSection.style.display = 'none';
    quizSection.style.display = 'block';

    // Scroll to quiz section
    quizSection.scrollIntoView({ behavior: 'smooth' });
}

// ==================== VIDEO ANALYSIS FUNCTIONS ====================

let mediaRecorder = null;
let recordedChunks = [];
let currentVideoBlob = null;

function initVideoAnalysis() {
    // Video file input handler
    const videoInput = document.getElementById('video-input');
    if (videoInput) {
        videoInput.addEventListener('change', handleVideoFileSelect);
    }

    // Recording buttons
    const startRecordBtn = document.getElementById('start-record-btn');
    const stopRecordBtn = document.getElementById('stop-record-btn');

    if (startRecordBtn) {
        startRecordBtn.addEventListener('click', startRecording);
    }

    if (stopRecordBtn) {
        stopRecordBtn.addEventListener('click', stopRecording);
    }

    // Analyze and clear buttons
    const analyzeVideoBtn = document.getElementById('analyze-video-btn');
    const clearVideoBtn = document.getElementById('clear-video-btn');
    const newVideoBtn = document.getElementById('new-video-btn');

    if (analyzeVideoBtn) {
        analyzeVideoBtn.addEventListener('click', analyzeVideo);
    }

    if (clearVideoBtn) {
        clearVideoBtn.addEventListener('click', clearVideo);
    }

    if (newVideoBtn) {
        newVideoBtn.addEventListener('click', resetVideoAnalysis);
    }
}

function handleVideoFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('file-name').textContent = file.name;

        // Create video URL
        const videoURL = URL.createObjectURL(file);
        const videoPreview = document.getElementById('video-preview');
        videoPreview.src = videoURL;

        document.getElementById('video-preview-container').style.display = 'block';
        document.getElementById('recording-preview').style.display = 'none';
        document.getElementById('video-preview').style.display = 'block';

        currentVideoBlob = file;
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

        // Show video preview
        const videoPreview = document.getElementById('video-preview');
        videoPreview.srcObject = stream;
        videoPreview.style.display = 'block';
        videoPreview.play();

        document.getElementById('video-preview-container').style.display = 'block';
        document.getElementById('recording-preview').style.display = 'none';

        // Start recording
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];

        mediaRecorder.ondataavailable = function (event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = function () {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            currentVideoBlob = blob;

            // Show recorded video
            const recordingURL = URL.createObjectURL(blob);
            const recordingPreview = document.getElementById('recording-preview');
            recordingPreview.src = recordingURL;

            document.getElementById('video-preview').style.display = 'none';
            recordingPreview.style.display = 'block';

            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();

        // Toggle buttons
        document.getElementById('start-record-btn').style.display = 'none';
        document.getElementById('stop-record-btn').style.display = 'inline-block';

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Could not access camera. Please make sure you have granted camera permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();

        // Toggle buttons
        document.getElementById('start-record-btn').style.display = 'inline-block';
        document.getElementById('stop-record-btn').style.display = 'none';
    }
}

function clearVideo() {
    currentVideoBlob = null;
    recordedChunks = [];

    document.getElementById('video-input').value = '';
    document.getElementById('file-name').textContent = 'No file selected';
    document.getElementById('video-preview').src = '';
    document.getElementById('recording-preview').src = '';
    document.getElementById('video-preview-container').style.display = 'none';
    document.getElementById('video-results').style.display = 'none';
}

function resetVideoAnalysis() {
    clearVideo();
    document.getElementById('video-analysis').scrollIntoView({ behavior: 'smooth' });
}

async function analyzeVideo() {
    const manualDesc = document.getElementById('video-manual-desc');
    const hasManualText = manualDesc && manualDesc.value.trim() !== '';

    if (!currentVideoBlob && !hasManualText) {
        alert('Please select a video, record a video, or provide a manual description first.');
        return;
    }

    // Show progress
    document.getElementById('video-preview-container').style.display = 'none';
    document.getElementById('analysis-progress').style.display = 'block';
    document.getElementById('video-results').style.display = 'none';

    // Animate progress
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    let progress = 0;

    const progressMessages = [
        'Loading video...',
        'Detecting faces...',
        'Analyzing facial expressions...',
        'Checking eye contact patterns...',
        'Evaluating movement patterns...',
        'Generating results...'
    ];

    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;

        progressFill.style.width = progress + '%';

        const messageIndex = Math.min(Math.floor(progress / 20), progressMessages.length - 1);
        progressText.textContent = progressMessages[messageIndex];

        if (progress >= 100) {
            clearInterval(progressInterval);
        }
    }, 500);

    try {
        // Create form data
        const formData = new FormData();
        if (currentVideoBlob) {
            formData.append('video', currentVideoBlob, 'video.webm');
        }

        // Add manual description if provided
        const manualDesc = document.getElementById('video-manual-desc');
        if (manualDesc && manualDesc.value.trim()) {
            formData.append('manual_text', manualDesc.value.trim());
        }

        // Send to backend for analysis
        const response = await fetch('http://127.0.0.1:5001/analyze-video', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Hide progress and show results
        document.getElementById('analysis-progress').style.display = 'none';
        document.getElementById('video-results').style.display = 'block';

        if (result.success) {
            displayVideoResults(result);
        } else {
            alert('Error analyzing video: ' + result.error);
            document.getElementById('analysis-progress').style.display = 'none';
            document.getElementById('video-preview-container').style.display = 'block';
        }

    } catch (error) {
        console.error('Error analyzing video:', error);
        alert('An error occurred while analyzing the video. Please try again.');
        document.getElementById('analysis-progress').style.display = 'none';
        document.getElementById('video-preview-container').style.display = 'block';
    }
}

function displayVideoResults(result) {
    const prediction = result.prediction;
    const analysis = result.analysis;

    // Set result icon
    const resultIcon = document.getElementById('video-result-icon');
    if (prediction.status === 'positive') {
        resultIcon.textContent = '⚠️';
    } else if (prediction.status === 'moderate') {
        resultIcon.textContent = '🤔';
    } else {
        resultIcon.textContent = '✅';
    }

    // Set risk level and confidence
    document.getElementById('video-risk-level').textContent = prediction.risk_level;
    document.getElementById('video-risk-level').className = 'result-risk-level ' + prediction.status;
    document.getElementById('video-confidence').textContent = prediction.confidence + '% Confidence';

    // Set description
    document.getElementById('video-result-description').innerHTML = `
        <p>${prediction.description}</p>
    `;

    // Display autism markers
    const markersList = document.getElementById('markers-list');
    if (prediction.detailed_markers && prediction.detailed_markers.length > 0) {
        let markersHTML = '';

        prediction.detailed_markers.forEach(marker => {
            const severityClass = marker.severity === 'moderate' ? 'severity-high' :
                marker.severity === 'mild' ? 'severity-low' : 'severity-medium';

            markersHTML += `
                <div class="marker-item ${severityClass}">
                    <div class="marker-header">
                        <span class="marker-name">${marker.marker}</span>
                        <span class="marker-severity ${severityClass}">${marker.severity}</span>
                    </div>
                    <p class="marker-description">${marker.description}</p>
                </div>
            `;
        });

        markersList.innerHTML = markersHTML;
    } else {
        markersList.innerHTML = '<p class="no-markers">No specific autism-related markers detected in this video.</p>';
    }

    // Display analysis details
    const detailsList = document.getElementById('analysis-details');
    let detailsHTML = '';

    if (analysis.analysis_details) {
        analysis.analysis_details.forEach(detail => {
            detailsHTML += `
                <div class="detail-item">
                    <span class="detail-type">${detail.type}</span>
                    <span class="detail-text">${detail.detail}</span>
                </div>
            `;
        });
    }

    detailsHTML += `
        <div class="detail-item">
            <span class="detail-type">frames</span>
            <span class="detail-text">${analysis.frames_analyzed} frames analyzed</span>
        </div>
        <div class="detail-item">
            <span class="detail-type">faces</span>
            <span class="detail-text">${analysis.faces_detected} faces detected</span>
        </div>
        <div class="detail-item">
            <span class="detail-type">eye_contact</span>
            <span class="detail-text">${analysis.eye_contact_score}% eye contact score</span>
        </div>
    `;

    detailsList.innerHTML = detailsHTML;

    // Scroll to results
    document.getElementById('video-results').scrollIntoView({ behavior: 'smooth' });
}

// Export functions for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        collectFormData,
        makePrediction,
        displayResults,
        resetForm,
        initVideoAnalysis,
        handleVideoFileSelect,
        startRecording,
        stopRecording,
        analyzeVideo
    };
}


// ==================== CHATBOT FUNCTIONS ====================

function toggleChat() {
    const container = document.getElementById('chatbot-container');
    const fab = document.getElementById('chatbot-fab');

    // Check if the container is currently hidden
    if (container.classList.contains('hidden')) {
        // Open the chatbot: show container, hide FAB
        container.classList.remove('hidden');
        fab.classList.add('hidden');

        // Focus the input field
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            setTimeout(() => chatInput.focus(), 300);
        }
    } else {
        // Close the chatbot: hide container, show FAB
        container.classList.add('hidden');
        fab.classList.remove('hidden');
    }
}

// Add event listener to close chatbot when clicking outside
document.addEventListener('click', function (event) {
    const container = document.getElementById('chatbot-container');
    const fab = document.getElementById('chatbot-fab');

    // If the chatbot is open (not hidden)
    if (container && !container.classList.contains('hidden')) {
        // Did the user click inside the container or on the FAB itself?
        if (!container.contains(event.target) && !fab.contains(event.target)) {
            // Click was outside, so close it
            toggleChat();
        }
    }
});

function handleChatSubmit(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    const chatBody = document.getElementById('chatbot-body');

    // Add user message
    const userMsgElem = document.createElement('div');
    userMsgElem.className = 'chat-message user-message';
    userMsgElem.textContent = message;
    chatBody.appendChild(userMsgElem);

    // Clear input
    input.value = '';

    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;

    // Show thinking indicator
    const botMsgElem = document.createElement('div');
    botMsgElem.className = 'chat-message bot-message';
    botMsgElem.innerHTML = '<i>Thinking...</i>';
    chatBody.appendChild(botMsgElem);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
        const response = await fetch('http://127.0.0.1:5001/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const result = await response.json();
        botMsgElem.innerHTML = '';
        botMsgElem.textContent = result.reply;
    } catch (error) {
        console.error('Chat error:', error);
        botMsgElem.innerHTML = '';
        botMsgElem.textContent = 'Sorry, I am having trouble connecting right now.';
    }

    chatBody.scrollTop = chatBody.scrollHeight;
}

