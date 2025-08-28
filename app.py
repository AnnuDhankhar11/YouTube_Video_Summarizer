from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import streamlit as st
from langchain_groq import ChatGroq
import os
import re
from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(
    model = 'llama-3.1-8b-instant',
    temperature=0,
    groq_api_key = os.getenv('GROQ_API_KEY')
    )

prompt = """You are an youtube video summarizer. 
            Take the script, summarize the video and return importaant pointer."""

def extract_transcript_details(youtube_video_url):
    try:
        # Extract the video ID from the URL more robustly
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_video_url)
        if not video_id_match:
            raise Exception('Invalid YouTube URL')
        video_id = video_id_match.group(1)

        # List all available transcripts for the video
        transcript_list = YouTubeTranscriptApi().list(video_id)    

        # Try to get the manually created transcript first
        transcript = ""
        languages = ['en', 'hi', 'ta', 'te', 'bn', 'gu', 'fr', 'de', 'es']
        
        try:
            transcript_obj = transcript_list.find_manually_created_transcript(languages)
            transcript_text = transcript_obj.fetch()
            for item in transcript_text:
                transcript += " " + item.text
        
        # If no manually created transcript is available, fallback to auto-generated
        except Exception as e:
            if "NoTranscriptFound" in str(type(e).__name__):
                try:
                    transcript_obj = transcript_list.find_generated_transcript(languages)
                    transcript_text = transcript_obj.fetch()
                    for item in transcript_text:
                        transcript += " " + item.text
                except Exception as e2:
                    if "NoTranscriptFound" in str(type(e2).__name__):
                        # If no transcript in preferred languages, try any available transcript
                        available_transcripts = list(transcript_list)
                        if available_transcripts:
                            transcript_obj = available_transcripts[0]
                            transcript_text = transcript_obj.fetch()
                            for item in transcript_text:
                                transcript += " " + item.text
                        else:
                            raise Exception('No transcripts found for this video in any language.')
                    else:
                        raise e2
            else:
                raise e
        
        return transcript.strip()
    
    except Exception as e:
        if "TranscriptsDisabled" in str(type(e).__name__):
            raise Exception('Transcripts are disabled for this video.')
        elif "NoTranscriptFound" in str(type(e).__name__):
            raise Exception('No transcripts found for this video.')
        else:
            raise Exception(f'An error occurred: {str(e)}')
        
def generate_content(transcript_text, prompt):
    model = llm
    response = model.invoke(prompt+transcript_text)
    return response

st.title('YouTube Transcript to Detailed Notes Converter')
youtube_link = st.text_input('Enter YouTube Video Link:')

if youtube_link:
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_link)
    if not video_id_match:
        raise Exception('Invalid YouTube URL')
    video_id = video_id_match.group(1)
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width =True)

if st.button("Get Detailed Notes"):
    video_transcript = extract_transcript_details(youtube_link)

    if video_transcript:
        summary = generate_content(transcript_text=video_transcript, prompt=prompt)
        st.markdown('## Detailed Notes:')
        st.write(summary.content)