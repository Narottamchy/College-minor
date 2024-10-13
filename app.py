from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pydub import AudioSegment
from speech_report import process_audio_file
from final_report import final_report_generation
import subprocess
from supabase_storage import upload_to_supabase  # Import the function from supabase_storage.py
from newapp import ask_question, upload_pdf

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define the path where uploaded audio files will be stored
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the folder for storing PDF reports
PDF_FOLDER = os.path.join('speech_analysis_output', 'pdf_reports')
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def reencode_audio(file_path):
    """Attempts to re-encode a potentially corrupted audio file to ensure it's in a valid format."""
    try:
        audio = AudioSegment.from_file(file_path)
        reencoded_path = file_path.replace(".wav", "_reencoded.wav")
        audio.export(reencoded_path, format="wav")
        return reencoded_path
    except Exception as e:
        print(f"Error re-encoding audio with pydub: {e}")
        return None

def fix_audio_with_ffmpeg(input_path):
    """Use ffmpeg to fix corrupted wav files by re-encoding them."""
    output_path = input_path.replace(".wav", "_ffmpeg_fixed.wav")
    try:
        # Re-encode with ffmpeg
        command = f"ffmpeg -i {input_path} -acodec pcm_s16le -ar 44100 {output_path} -y"
        subprocess.run(command, shell=True, check=True)
        return output_path
    except Exception as e:
        print(f"Error fixing audio with ffmpeg: {e}")
        return None

@app.route('/')
def index():
    return "Welcome to the Speech Analysis API!"

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        if not request.data:
            return jsonify({"error": "No binary audio data found in the request"}), 400

        audio_filename = 'uploaded_audio.wav'
        audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

        # Save the audio file to disk
        with open(audio_path, 'wb') as audio_file:
            audio_file.write(request.data)

        normalized_audio_path = os.path.normpath(audio_path)

        # Step 1: Try to process the audio file
        try:
            process_audio_file(normalized_audio_path)
            print("Audio processed successfully using main.py.")
        except Exception as e:
            print(f"Error processing audio with main.py: {e}")

            # Step 2: Try re-encoding with pydub if processing fails
            print("Attempting to re-encode the audio file with pydub...")
            reencoded_path = reencode_audio(normalized_audio_path)
            if reencoded_path:
                try:
                    process_audio_file(reencoded_path)
                    print("Audio successfully re-encoded and processed with pydub.")
                except Exception as e2:
                    print(f"Error processing re-encoded audio with main.py: {e2}")

                    # Step 3: Try fixing with ffmpeg if pydub fails
                    print("Attempting to fix the audio file with ffmpeg...")
                    ffmpeg_fixed_path = fix_audio_with_ffmpeg(normalized_audio_path)
                    if ffmpeg_fixed_path:
                        try:
                            process_audio_file(ffmpeg_fixed_path)
                            print("Audio successfully processed after fixing with ffmpeg.")
                        except Exception as e3:
                            print(f"Error processing ffmpeg-fixed audio with main.py: {e3}")
                            return jsonify({"error": "Error processing audio after all attempts", "details": str(e3)}), 500
                    else:
                        return jsonify({"error": "Failed to fix audio with ffmpeg"}), 500
            else:
                return jsonify({"error": "Failed to re-encode audio with pydub"}), 500

        # Step 4: Generate the final report
        try:
            final_report_generation()
            print("Final report successfully generated.")
        except Exception as e:
            print(f"Error generating final report: {e}")
            return jsonify({"error": "Error generating final report", "details": str(e)}), 500

        # Step 5: Upload report and final report to Supabase
        try:
            # Upload reports to Supabase from the updated folder path
            report_pdf_path = os.path.join(PDF_FOLDER, 'report.pdf')
            final_report_pdf_path = os.path.join(PDF_FOLDER, 'final_report.pdf')

            report_pdf_url = upload_to_supabase(report_pdf_path, "reports")
            final_report_pdf_url = upload_to_supabase(final_report_pdf_path, "final_report")

            # Return the URLs in the response
            return jsonify({
                "message": "Process completed successfully",
                "report_pdf_url": report_pdf_url,
                "final_report_pdf_url": final_report_pdf_url
            }), 200

        except Exception as e:
            print(f"Error uploading reports to Supabase: {e}")
            return jsonify({"error": "Error uploading reports", "details": str(e)}), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    return ask_question()

@app.route('/upload', methods=['POST'])
def upload():
    return upload_pdf()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

