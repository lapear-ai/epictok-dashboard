#!/usr/bin/env python3
"""
EpicTok Dashboard - Fully Automated Historical Video Factory
Web interface with complete automation pipeline
"""

import os
import sys
import json
import time
import random
import requests
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file, Response
from queue import Queue
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'epictok-secret-key'

# Config - use absolute path for Railway
PROJECTS_DIR = Path(os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '.')) / "output"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/health')
def health_check():
    """Health check for Railway"""
    return jsonify({"status": "ok", "elevenlabs": bool(ELEVENLABS_API_KEY)})

# Job queue for background processing
job_queue = Queue()
job_status = {}

# API Keys from environment or config
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

def get_historical_event():
    """Fetch random historical event from Wikipedia"""
    try:
        response = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/random/summary",
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "id": data.get("pageid", ""),
                "title": data.get("title", ""),
                "extract": data.get("extract", ""),
                "year": extract_year(data.get("extract", "")),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception as e:
        print(f"Error fetching Wikipedia: {e}")
    
    # Fallback events
    fallback_events = [
        {"title": "The Fall of Constantinople", "extract": "In 1453, Constantinople fell to the Ottoman Empire, ending the Byzantine Empire and marking the end of the Middle Ages.", "year": "1453"},
        {"title": "The First Flight", "extract": "On December 17, 1903, the Wright brothers made the first powered flight in Kitty Hawk, North Carolina.", "year": "1903"},
        {"title": "The Moon Landing", "extract": "On July 20, 1969, Neil Armstrong became the first human to set foot on the moon.", "year": "1969"},
        {"title": "The Printing Press", "extract": "In 1440, Johannes Gutenberg invented the printing press, revolutionizing the spread of knowledge.", "year": "1440"},
        {"title": "The French Revolution", "extract": "Beginning in 1789, the French Revolution overthrew the monarchy and established a republic.", "year": "1789"}
    ]
    return random.choice(fallback_events)

def extract_year(text):
    """Extract year from text"""
    import re
    match = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', text)
    return match.group(1) if match else "Unknown"

def get_years_ago(year_str):
    try:
        year = int(year_str)
        return datetime.now().year - year
    except:
        return "many"

def generate_script(event_data):
    """Generate engaging script"""
    hooks = [
        f"In {event_data['year']}, something happened that changed everything.",
        f"Most people don't know what really happened in {event_data['year']}.",
        f"This moment in {event_data['year']} shaped our world forever.",
        f"What you're about to hear happened {get_years_ago(event_data['year'])} years ago.",
        f"The year was {event_data['year']}. Nobody saw this coming."
    ]
    
    hook = random.choice(hooks)
    
    script = f"""{hook}

{event_data['title']}.

{event_data['extract']}

This is history that deserves to be remembered.
"""
    
    return script.strip()

def generate_image_prompt(event_data):
    """Generate AI image prompt"""
    styles = [
        "dramatic oil painting style",
        "vintage photograph style",
        "epic cinematic scene",
        "historical illustration",
        "dramatic black and white photography"
    ]
    
    style = random.choice(styles)
    return f"{event_data['title']}, {event_data['year']}, {style}, historical scene, dramatic lighting, detailed, cinematic composition"

def save_project(event_data, script):
    """Save project files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in event_data["title"] if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50].replace(' ', '_')
    
    project_dir = PROJECTS_DIR / f"{timestamp}_{safe_title}"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "id": f"{timestamp}_{safe_title}",
        "title": event_data["title"],
        "year": event_data["year"],
        "script": script,
        "image_prompt": generate_image_prompt(event_data),
        "created_at": datetime.now().isoformat(),
        "source_url": event_data.get("url", ""),
        "status": "created"
    }
    
    with open(project_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    with open(project_dir / "script.txt", 'w') as f:
        f.write(script)
    
    return project_dir, metadata

def generate_voiceover(project_dir, script):
    """Generate voiceover using ElevenLabs"""
    if not ELEVENLABS_API_KEY:
        return False, "No API key"
    
    voice_path = project_dir / "voiceover.mp3"
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": script,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            with open(voice_path, 'wb') as f:
                f.write(response.content)
            return True, str(voice_path)
        else:
            return False, f"API Error: {response.status_code}"
    except Exception as e:
        return False, str(e)

def generate_image(project_dir, prompt):
    """Generate image using Pollinations AI (free, no key needed)"""
    try:
        # Use Pollinations for free image generation
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&seed={random.randint(1, 10000)}&nologo=true"
        
        response = requests.get(image_url, timeout=120)
        if response.status_code == 200:
            image_path = project_dir / "scene.jpg"
            with open(image_path, 'wb') as f:
                f.write(response.content)
            return True, str(image_path)
        else:
            return False, f"Image API Error: {response.status_code}"
    except Exception as e:
        return False, str(e)

def create_video(project_dir):
    """Create video using FFmpeg"""
    try:
        image_file = project_dir / "scene.jpg"
        audio_file = project_dir / "voiceover.mp3"
        output_file = project_dir / "final_video.mp4"
        metadata_file = project_dir / "metadata.json"
        
        if not image_file.exists() or not audio_file.exists():
            return False, "Missing image or audio"
        
        # Load metadata for text overlay
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # FFmpeg command with Ken Burns effect
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_file),
            "-i", str(audio_file),
            "-vf", f"zoompan=z='min(zoom+0.001,1.15)':d=100:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fade=in:0:25,fade=out:st=3:d=1,drawtext=text='{metadata['title']}':fontcolor=white:fontsize=64:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=80,drawtext=text='{metadata['year']}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=150",
            "-c:v", "libx264",
            "-preset", "fast",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return True, str(output_file)
        else:
            return False, result.stderr[:500]
    except Exception as e:
        return False, str(e)

def create_video_with_nova(project_dir, scene_description=""):
    """Create video using Amazon Nova Reel AI video generation"""
    try:
        import boto3
        
        audio_file = project_dir / "voiceover.mp3"
        output_file = project_dir / "final_video.mp4"
        metadata_file = project_dir / "metadata.json"
        
        if not audio_file.exists():
            return False, "Missing audio file"
        
        # Load metadata
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Use image prompt as base for video prompt
        video_prompt = scene_description or metadata.get('image_prompt', '')
        video_prompt = f"Cinematic historical scene: {video_prompt[:400]}"
        
        # Initialize Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1'
        )
        
        model_id = "amazon.nova-reel-v1:0"
        
        request_body = {
            "taskType": "TEXT_VIDEO",
            "textToVideoParams": {
                "text": video_prompt
            },
            "videoGenerationConfig": {
                "durationSeconds": 6,
                "fps": 24,
                "dimension": "1280x720",
                "seed": random.randint(0, 2147483646)
            }
        }
        
        # Start async generation
        response = bedrock_runtime.start_async_invoke(
            modelId=model_id,
            modelInput=json.dumps(request_body)
        )
        
        invocation_arn = response['invocationArn']
        
        # Poll for completion (max 10 min)
        max_attempts = 60
        for attempt in range(max_attempts):
            status_response = bedrock_runtime.get_async_invoke(
                invocationArn=invocation_arn
            )
            
            status = status_response['status']
            
            if status == 'Completed':
                # Get video from S3
                s3_uri = status_response['outputDataConfig']['s3OutputDataConfig']['s3Uri']
                
                # Download and process with audio
                s3 = boto3.client('s3')
                parts = s3_uri.replace("s3://", "").split("/", 1)
                bucket = parts[0]
                key = parts[1]
                
                temp_video = project_dir / "nova_temp.mp4"
                s3.download_file(bucket, key, str(temp_video))
                
                # Combine with audio using FFmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(temp_video),
                    "-i", str(audio_file),
                    "-vf", f"drawtext=text='{metadata['title']}':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=40,drawtext=text='{metadata['year']}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=90",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    str(output_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                # Cleanup temp file
                temp_video.unlink(missing_ok=True)
                
                if result.returncode == 0:
                    return True, str(output_file)
                else:
                    return False, result.stderr[:500]
                    
            elif status in ['Failed', 'Error']:
                return False, status_response.get('failureMessage', 'Nova generation failed')
            
            time.sleep(10)
        
        return False, "Timeout waiting for Nova"
        
    except ImportError:
        return False, "boto3 not installed. Run: pip3 install boto3"
    except Exception as e:
        return False, str(e)

def process_job(job_id, auto_generate=True, use_nova=False):
    """Process a video generation job"""
    job_status[job_id] = {"status": "starting", "progress": 0, "message": "Starting..."}
    
    try:
        # Step 1: Fetch event
        job_status[job_id] = {"status": "fetching", "progress": 10, "message": "Fetching historical event..."}
        event = get_historical_event()
        
        # Step 2: Generate script
        job_status[job_id] = {"status": "scripting", "progress": 20, "message": "Generating script..."}
        script = generate_script(event)
        
        # Step 3: Save project
        job_status[job_id] = {"status": "saving", "progress": 30, "message": "Creating project..."}
        project_dir, metadata = save_project(event, script)
        
        if auto_generate:
            # Step 4: Generate image
            job_status[job_id] = {"status": "image", "progress": 50, "message": "Generating image with AI..."}
            img_success, img_result = generate_image(project_dir, metadata['image_prompt'])
            
            if not img_success:
                job_status[job_id] = {"status": "error", "progress": 50, "message": f"Image failed: {img_result}"}
                return
            
            # Step 5: Generate voiceover
            job_status[job_id] = {"status": "voice", "progress": 70, "message": "Generating voiceover..."}
            voice_success, voice_result = generate_voiceover(project_dir, script)
            
            if not voice_success:
                job_status[job_id] = {"status": "error", "progress": 70, "message": f"Voice failed: {voice_result}"}
                return
            
            # Step 6: Create video (with or without Nova)
            if use_nova:
                job_status[job_id] = {"status": "video", "progress": 85, "message": "Generating AI video with Nova (2-5 min)..."}
                video_success, video_result = create_video_with_nova(project_dir)
            else:
                job_status[job_id] = {"status": "video", "progress": 90, "message": "Assembling video..."}
                video_success, video_result = create_video(project_dir)
            
            if not video_success:
                job_status[job_id] = {"status": "error", "progress": 90, "message": f"Video failed: {video_result}"}
                return
            
            # Update metadata
            metadata['status'] = 'completed'
            metadata['completed_at'] = datetime.now().isoformat()
            with open(project_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            job_status[job_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Video complete!",
                "project_id": metadata['id'],
                "title": metadata['title'],
                "year": metadata['year']
            }
        else:
            job_status[job_id] = {
                "status": "manual",
                "progress": 100,
                "message": "Project ready - add image and voiceover",
                "project_id": metadata['id'],
                "title": metadata['title'],
                "year": metadata['year']
            }
    
    except Exception as e:
        job_status[job_id] = {"status": "error", "progress": 0, "message": str(e)}

def job_worker():
    """Background worker to process jobs"""
    while True:
        job_data = job_queue.get()
        if job_data is None:
            break
        if isinstance(job_data, tuple):
            job_id, use_nova = job_data
        else:
            job_id = job_data
            use_nova = False
        process_job(job_id, auto_generate=True, use_nova=use_nova)
        job_queue.task_done()

# Start background worker
worker_thread = threading.Thread(target=job_worker, daemon=True)
worker_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/projects')
def list_projects():
    """List all projects"""
    projects = []
    if PROJECTS_DIR.exists():
        for proj_dir in sorted(PROJECTS_DIR.iterdir(), reverse=True):
            if proj_dir.is_dir():
                metadata_file = proj_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        metadata['has_video'] = (proj_dir / "final_video.mp4").exists()
                        metadata['has_image'] = (proj_dir / "scene.jpg").exists()
                        metadata['has_voice'] = (proj_dir / "voiceover.mp3").exists()
                        projects.append(metadata)
    return jsonify(projects)

@app.route('/api/generate', methods=['POST'])
def generate():
    """Start video generation"""
    data = request.get_json() or {}
    use_nova = data.get('use_nova', False)

    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
    job_queue.put((job_id, use_nova))
    job_status[job_id] = {"status": "queued", "progress": 0, "message": "Queued..."}
    return jsonify({"job_id": job_id, "status": "queued", "use_nova": use_nova})

@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    return jsonify(job_status.get(job_id, {"status": "unknown"}))

@app.route('/api/project/<project_id>')
def get_project(project_id):
    """Get project details"""
    for proj_dir in PROJECTS_DIR.iterdir():
        if proj_dir.is_dir() and project_id in proj_dir.name:
            metadata_file = proj_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    metadata['path'] = str(proj_dir)
                    return jsonify(metadata)
    return jsonify({"error": "Project not found"}), 404

@app.route('/api/video/<project_id>')
def download_video(project_id):
    """Download video file"""
    for proj_dir in PROJECTS_DIR.iterdir():
        if proj_dir.is_dir() and project_id in proj_dir.name:
            video_file = proj_dir / "final_video.mp4"
            if video_file.exists():
                return send_file(video_file, as_attachment=True)
    return jsonify({"error": "Video not found"}), 404

@app.route('/api/stats')
def get_stats():
    """Get dashboard stats"""
    total = 0
    completed = 0
    
    if PROJECTS_DIR.exists():
        for proj_dir in PROJECTS_DIR.iterdir():
            if proj_dir.is_dir():
                total += 1
                if (proj_dir / "final_video.mp4").exists():
                    completed += 1
    
    return jsonify({
        "total_projects": total,
        "completed_videos": completed,
        "pending": total - completed
    })

if __name__ == '__main__':
    print("="*70)
    print("  EPIC TOK DASHBOARD")
    print("="*70)
    print(f"\n📁 Projects directory: {PROJECTS_DIR.absolute()}")
    print(f"🔊 ElevenLabs API: {'✅ Configured' if ELEVENLABS_API_KEY else '❌ Not configured'}")
    print("\n🌐 Starting server on http://localhost:8766")
    print("="*70 + "\n")
    
    # Use Railway's PORT or default to 8766
    port = int(os.getenv('PORT', 8766))
    app.run(host='0.0.0.0', port=port, debug=False)
