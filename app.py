from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from ultralytics import YOLO
import cv2
import numpy as np

app = FastAPI(title="Fire Watch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("best.pt")


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Fire Watch AI</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    min-height: 100vh;
    background: linear-gradient(135deg,#111827,#450a0a);
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
}

.container {
    width: 92%;
    max-width: 750px;
    background: #1f2937;
    padding: 30px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 0 15px 40px rgba(0,0,0,.5);
}

h1 {
    font-size: 38px;
}

.subtitle {
    color: #d1d5db;
}

video,
#preview {
    width: 100%;
    max-height: 400px;
    object-fit: cover;
    border-radius: 15px;
    margin: 20px 0;
    display: none;
}

button {
    border: none;
    padding: 13px 22px;
    margin: 7px;
    border-radius: 10px;
    font-size: 16px;
    cursor: pointer;
    color: white;
    background: #dc2626;
}

button:hover {
    background: #b91c1c;
}

input[type="file"] {
    background: white;
    color: black;
    padding: 10px;
    border-radius: 8px;
    margin: 15px;
    max-width: 100%;
}

#result {
    display: none;
    margin-top: 20px;
    padding: 20px;
    border-radius: 12px;
    background: #374151;
}

.fire {
    color: #ff3333;
    font-size: 25px;
    font-weight: bold;
}

.safe {
    color: #22c55e;
    font-size: 25px;
    font-weight: bold;
}

.loading {
    color: #facc15;
    font-size: 20px;
}

#cameraBox {
    display: none;
}
</style>
</head>

<body>

<div class="container">

<h1>🔥 Fire Watch AI</h1>

<p class="subtitle">
AI Powered Fire & Smoke Detection System
</p>

<!-- IMAGE -->
<input type="file" id="imageInput" accept="image/*">

<br>

<img id="preview">

<br>

<button onclick="detectImage()">
🔍 Detect Image
</button>

<hr>

<!-- CAMERA -->

<button onclick="startCamera()">
📷 Open Camera
</button>

<button onclick="stopCamera()">
❌ Stop Camera
</button>

<div id="cameraBox">

<video id="video" autoplay playsinline></video>

<br>

<button onclick="captureImage()">
📸 Capture & Detect
</button>

</div>

<div id="result"></div>

</div>


<script>

let stream = null;

const imageInput =
document.getElementById("imageInput");

const preview =
document.getElementById("preview");

const video =
document.getElementById("video");

const cameraBox =
document.getElementById("cameraBox");

const result =
document.getElementById("result");


// =======================
// IMAGE PREVIEW
// =======================

imageInput.addEventListener("change", function() {

    const file = this.files[0];

    if (file) {

        preview.src =
        URL.createObjectURL(file);

        preview.style.display = "block";

    }

});


// =======================
// START CAMERA
// =======================

async function startCamera() {

    try {

        stream =
        await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        video.srcObject = stream;

        video.style.display = "block";

        cameraBox.style.display = "block";

    }

    catch(error) {

        alert(
            "Camera access denied or unavailable."
        );

        console.error(error);

    }
}


// =======================
// STOP CAMERA
// =======================

function stopCamera() {

    if (stream) {

        stream.getTracks().forEach(
            track => track.stop()
        );

        stream = null;

    }

    video.srcObject = null;

    video.style.display = "none";

    cameraBox.style.display = "none";
}


// =======================
// CAPTURE CAMERA IMAGE
// =======================

function captureImage() {

    if (!stream) {

        alert("Open camera first.");

        return;

    }

    const canvas =
    document.createElement("canvas");

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    const ctx =
    canvas.getContext("2d");

    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    canvas.toBlob(function(blob) {

        const file =
        new File(
            [blob],
            "camera.jpg",
            { type: "image/jpeg" }
        );

        detectFile(file);

    }, "image/jpeg");

}


// =======================
// IMAGE DETECTION
// =======================

function detectImage() {

    const file =
    imageInput.files[0];

    if (!file) {

        alert("Please select an image.");

        return;

    }

    detectFile(file);

}


// =======================
// SEND TO FASTAPI
// =======================

async function detectFile(file) {

    result.style.display = "block";

    result.innerHTML =
    '<p class="loading">🔄 Analyzing...</p>';

    const formData =
    new FormData();

    formData.append("file", file);

    try {

        const response =
        await fetch("/detect", {

            method: "POST",

            body: formData

        });

        const data =
        await response.json();


        if (!data.success) {

            result.innerHTML =
            `<p class="fire">
            ❌ ${data.error}
            </p>`;

            return;

        }


        if (data.fire_detected) {

            result.innerHTML = `

            <p class="fire">
            🔥 FIRE / SMOKE DETECTED!
            </p>

            <p>
            Confidence:
            <strong>${data.confidence}%</strong>
            </p>

            `;

            // Alarm
            const alarm =
            new Audio(
            "https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg"
            );

            alarm.play().catch(() => {});

        }

        else {

            result.innerHTML = `

            <p class="safe">
            ✅ NO FIRE DETECTED
            </p>

            <p>
            Confidence:
            <strong>${data.confidence}%</strong>
            </p>

            `;

        }


        if (
            data.detections &&
            data.detections.length > 0
        ) {

            result.innerHTML +=
            "<h3>Detections</h3>";

            data.detections.forEach(
            detection => {

                result.innerHTML += `

                <p>
                ${detection.class}
                -
                ${detection.confidence}%
                </p>

                `;

            });

        }

    }

    catch(error) {

        console.error(error);

        result.innerHTML = `

        <p class="fire">
        ❌ Backend connection failed
        </p>

        `;

    }

}


// =======================
// BACKEND
// =======================

</script>

</body>
</html>
"""


@app.post("/detect")
async def detect(file: UploadFile = File(...)):

    contents = await file.read()

    image_array = np.frombuffer(
        contents,
        np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:
        return {
            "success": False,
            "error": "Could not read image"
        }

    results = model.predict(
        source=image,
        conf=0.25,
        verbose=False
    )

    detections = []
    fire_detected = False
    highest_confidence = 0.0

    for result in results:

        for box in result.boxes:

            confidence = float(box.conf[0])

            class_id = int(box.cls[0])

            class_name = result.names[class_id]

            confidence_percent = round(
                confidence * 100,
                2
            )

            detections.append({
                "class": class_name,
                "confidence": confidence_percent
            })

            name = class_name.lower()

            if "fire" in name or "smoke" in name:
                fire_detected = True

            if confidence > highest_confidence:
                highest_confidence = confidence

    return {
        "success": True,
        "fire_detected": fire_detected,
        "confidence": round(
            highest_confidence * 100,
            2
        ),
        "detections": detections
    }