import re
import gc
import torch
import sqlite3
import yt_dlp
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from transformers import MBartForConditionalGeneration, MBartTokenizer

def extract_video_id(url):
    try:
        url = url.strip()
        patterns = [
            r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
            r"(?:embed\/)([0-9A-Za-z_-]{11})",
            r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None

class YouTubeSummarizer:
    def __init__(self):
        self.tokenizer = MBartTokenizer.from_pretrained("facebook/mbart-large-cc25")
        self.model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-cc25")
        if torch.cuda.is_available():
            self.model.to('cuda')
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('summaries.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS summaries
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      video_id TEXT, title TEXT, url TEXT, 
                      language TEXT, summary TEXT, timestamp DATETIME)''')
        conn.commit()
        conn.close()

    def save_summary(self, video_id, title, url, language, summary):
        conn = sqlite3.connect('summaries.db')
        c = conn.cursor()
        c.execute('''INSERT INTO summaries (video_id, title, url, language, summary, timestamp) 
                     VALUES (?, ?, ?, ?, ?, ?)''', (video_id, title, url, language, summary, datetime.now()))
        conn.commit()
        conn.close()

    def get_history(self, limit=10):
        conn = sqlite3.connect('summaries.db')
        c = conn.cursor()
        c.execute('''SELECT video_id, title, url, language, summary, timestamp 
                     FROM summaries ORDER BY timestamp DESC LIMIT ?''', (limit,))
        history = c.fetchall()
        conn.close()
        return [{
            'video_id': h[0],
            'title': h[1],
            'url': h[2],
            'language': h[3],
            'summary': h[4],
            'timestamp': h[5]
        } for h in history]

    def get_video_info(self, url):
        video_id = extract_video_id(url)
        if not video_id:
            return None
        try:
            ydl_opts = {"quiet": True, "no_warnings": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            return {
                'video_id': video_id,
                'title': info.get('title', 'Unknown'),
                'duration': f"{info.get('duration', 0) // 60} minutes {info.get('duration', 0) % 60} seconds",
                'thumbnail': info.get('thumbnail', f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
            }
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None

    def get_transcript(self, video_id):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript = transcript_list.find_manually_created_transcript()
            except:
                try:
                    transcript = transcript_list.find_generated_transcript()
                except:
                    transcript = transcript_list.find_transcript(['en'])
            formatter = TextFormatter()
            return formatter.format_transcript(transcript.fetch())
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None

    def generate_summary(self, text, target_lang):
        try:
            text = ' '.join(text.split()[:1024])
            inputs = self.tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
            if torch.cuda.is_available():
                inputs = inputs.to('cuda')
            summary_ids = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.lang_code_to_id.get(target_lang, self.tokenizer.lang_code_to_id['en_XX']),
                max_length=300,
                min_length=100,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
            return self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
        finally:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
