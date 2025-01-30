from flask import Flask, render_template, request, jsonify
from models import YouTubeSummarizer
import os

app = Flask(__name__)
summarizer = YouTubeSummarizer()

@app.route('/')
def index():
    history = summarizer.get_history()
    return render_template('index.html', history=history)

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        url = data.get('url')
        target_lang = data.get('language', 'en_XX')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Get video info and transcript
        video_info = summarizer.get_video_info(url)
        if not video_info:
            return jsonify({'error': 'Could not fetch video information'}), 400
            
        # Get transcript and generate summary
        transcript = summarizer.get_transcript(video_info['video_id'])
        if not transcript:
            return jsonify({'error': 'Could not fetch video transcript'}), 400
            
        summary = summarizer.generate_summary(transcript, target_lang)
        if not summary:
            return jsonify({'error': 'Could not generate summary'}), 500
            
        # Save to history
        summarizer.save_summary(
            video_info['video_id'],
            video_info['title'],
            url,
            target_lang,
            summary
        )
            
        return jsonify({
            'title': video_info['title'],
            'duration': video_info['duration'],
            'thumbnail': video_info['thumbnail'],
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def history():
    try:
        history_data = summarizer.get_history()
        return jsonify({'history': history_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)