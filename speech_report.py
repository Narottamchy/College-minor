import parselmouth
from parselmouth.praat import call
import pandas as pd
import speech_recognition as sr
import librosa
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
import sys
import os
import matplotlib

matplotlib.use('Agg')

# Function to transcribe audio using Google Web Speech API
def transcribe_speech(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        transcript = recognizer.recognize_google(audio_data)
        return transcript
    except sr.UnknownValueError:
        return "Speech not recognized"
    except sr.RequestError as e:
        return f"Error with the recognition service: {e}"

# Function to measure source acoustics (pitch, jitter, shimmer, etc.)
def measurePitch(voiceID, f0min, f0max, unit="Hertz"):
    sound = parselmouth.Sound(voiceID)  # Read the sound
    duration = call(sound, "Get total duration")  # Get total duration
    pitch = call(sound, "To Pitch", 0.0, f0min, f0max)  # Create a pitch object in Praat
    meanF0 = call(pitch, "Get mean", 0, 0, unit)  # Get mean pitch
    stdevF0 = call(pitch, "Get standard deviation", 0 ,0, unit)  # Get standard deviation of pitch
    harmonicity = call(sound, "To Harmonicity (cc)", 0.01, f0min, 0.1, 1.0)
    hnr = call(harmonicity, "Get mean", 0, 0)  # Harmonics-to-noise ratio (HNR)
    pointProcess = call(sound, "To PointProcess (periodic, cc)", f0min, f0max)

    # Jitter and Shimmer calculations
    localJitter = call(pointProcess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    localShimmer = call([sound, pointProcess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    return {
        "Duration (s)": duration,
        "Mean F0 (Hz)": meanF0,
        "Standard Deviation F0": stdevF0,
        "HNR (dB)": hnr,
        "Local Jitter (%)": localJitter * 100,
        "Local Shimmer (%)": localShimmer * 100
    }

# Phoneme accuracy, substitution rate, omission rate calculations
def calculate_phoneme_accuracy(transcription, phoneme_prediction):
    correct_phonemes = [t == p for t, p in zip(transcription, phoneme_prediction)]
    return sum(correct_phonemes) / len(correct_phonemes) * 100

def calculate_substitution_rate(transcription, phoneme_prediction):
    substitutions = sum([1 for t, p in zip(transcription, phoneme_prediction) if t != p and p != ""])
    return substitutions / len(transcription) * 100

def calculate_omission_rate(transcription, phoneme_prediction):
    omissions = sum([1 for p in phoneme_prediction if p == ""])
    return omissions / len(transcription) * 100

def calculate_speech_sound_accuracy(transcription, phoneme_prediction):
    correct = sum([1 for t, p in zip(transcription, phoneme_prediction) if t == p])
    incorrect = len(transcription) - correct
    return float('inf') if incorrect == 0 else correct / incorrect

# Fluency Metrics Calculation
def calculate_fluency_metrics(transcript, audio_file):
    audio, sr = librosa.load(audio_file, sr=None)
    duration = librosa.get_duration(y=audio, sr=sr)
    
    words = transcript.split()
    word_count = len(words)
    wpm = (word_count / duration) * 60

    # Detect pauses (approximation)
    pause_durations = librosa.effects.split(audio, top_db=30)  # Silence detection
    avg_pause_duration = sum([end - start for start, end in pause_durations]) / len(pause_durations)

    return {
        "Words per Minute (WPM)": wpm,
        "Average Pause Duration (s)": avg_pause_duration
    }

# Voice Quality Metrics (Partially dynamic)
def calculate_voice_quality_metrics(audio_file):
    sound = parselmouth.Sound(audio_file)
    intensity = sound.to_intensity()

    # Vocal intensity range
    vocal_intensity = intensity.values.max() - intensity.values.min()

    # Nasalization, Hoarseness, and Breathiness are placeholders
    nasalization = 10  # Requires specialized model
    hoarseness_index = 0.3  # Requires specialized model
    breathiness = 0.2  # Requires specialized model

    return {
        "Vocal Intensity (dB)": vocal_intensity,
        "Nasalization (%)": nasalization,
        "Hoarseness Index": hoarseness_index,
        "Breathiness Ratio": breathiness
    }

# Prosody Metrics (Partially dynamic)
def calculate_prosody_metrics(audio_file):
    sound = parselmouth.Sound(audio_file)
    pitch = sound.to_pitch()

    # Intonation range calculation
    pitch_values = pitch.selected_array['frequency']
    pitch_range = np.max(pitch_values) - np.min(pitch_values)

    return {
        "Intonation Patterns (Hz)": pitch_range,
        "Stress and Emphasis (Mock Value)": 0.4,  # Requires more complex analysis
        "Rhythm Consistency (Mock Value)": 0.1  # Requires more complex analysis
    }

# Acoustic Analysis Metrics
def calculate_acoustic_analysis_metrics(audio_file):
    sound = parselmouth.Sound(audio_file)
    formants = sound.to_formant_burg()

    f1 = call(formants, "Get mean", 1, 0, 0, "Hertz")  # Formant 1
    f2 = call(formants, "Get mean", 2, 0, 0, "Hertz")  # Formant 2
    f3 = call(formants, "Get mean", 3, 0, 0, "Hertz")  # Formant 3

    return {
        "Formant Frequency F1 (Hz)": f1,
        "Formant Frequency F2 (Hz)": f2,
        "Formant Frequency F3 (Hz)": f3
    }

# Generate and save report to text file
def generate_and_save_report(audio_file, transcription, phoneme_prediction, report_folder, report_filename, f0min=75, f0max=300, unit="Hertz"):
    try:
        # Transcribe the audio
        transcript = transcribe_speech(audio_file)

        # Use the measurePitch function to extract acoustic features
        acoustic_metrics = measurePitch(audio_file, f0min, f0max, unit)

        # Calculate phoneme-related articulation metrics
        phoneme_accuracy = calculate_phoneme_accuracy(transcription, phoneme_prediction)
        substitution_rate = calculate_substitution_rate(transcription, phoneme_prediction)
        omission_rate = calculate_omission_rate(transcription, phoneme_prediction)
        speech_sound_accuracy = calculate_speech_sound_accuracy(transcription, phoneme_prediction)

        # Calculate fluency metrics
        fluency_metrics = calculate_fluency_metrics(transcript, audio_file)

        # Calculate additional voice quality, prosody, and comprehension/language metrics
        voice_quality_metrics = calculate_voice_quality_metrics(audio_file)
        prosody_metrics = calculate_prosody_metrics(audio_file)
        acoustic_analysis_metrics = calculate_acoustic_analysis_metrics(audio_file)

        # Combine all metrics into a single report
        metrics = {
            "Transcribed Speech": transcript,
            "Phoneme Accuracy (%)": phoneme_accuracy,
            "Substitution Rate (%)": substitution_rate,
            "Omission Rate (%)": omission_rate,
            "Speech Sound Accuracy (Ratio)": speech_sound_accuracy
        }

        # Add the acoustic, fluency, voice quality, prosody, and other metrics to the report
        metrics.update(acoustic_metrics)
        metrics.update(fluency_metrics)
        metrics.update(voice_quality_metrics)
        metrics.update(prosody_metrics)
        metrics.update(acoustic_analysis_metrics)

        # Save the report as a .txt file
        report_file_path = os.path.join(report_folder, report_filename)
        with open(report_file_path, "w") as report_file:
            for metric, value in metrics.items():
                report_file.write(f"{metric}: {value}\n")

        print(f"Report saved to {report_file_path}")
        return metrics

    except Exception as e:
        print(f"Error generating report: {e}")
        return None

# Helper functions for generating graphs
def draw_spectrogram(spectrogram, dynamic_range=70):
    X, Y = spectrogram.x_grid(), spectrogram.y_grid()
    sg_db = 10 * np.log10(spectrogram.values)
    plt.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='afmhot')
    plt.ylim([spectrogram.ymin, spectrogram.ymax])
    plt.xlabel("time [s]")
    plt.ylabel("frequency [Hz]")

def draw_intensity(intensity):
    plt.plot(intensity.xs(), intensity.values.T, linewidth=3, color='w')
    plt.plot(intensity.xs(), intensity.values.T, linewidth=1)
    plt.grid(False)
    plt.ylim(0)
    plt.ylabel("intensity [dB]")

def draw_pitch(pitch):
    pitch_values = pitch.selected_array['frequency']
    pitch_values[pitch_values == 0] = np.nan
    plt.plot(pitch.xs(), pitch_values, 'o', markersize=5, color='w')
    plt.plot(pitch.xs(), pitch_values, 'o', markersize=2)
    plt.grid(False)
    plt.ylim(0, pitch.ceiling)
    plt.ylabel("fundamental frequency [Hz]")

# Save all plots to files
def generate_plots(audio_file, image_folder):
    sound = parselmouth.Sound(audio_file)

    # Plot waveform
    plt.figure()
    plt.plot(sound.xs(), sound.values.T)
    plt.xlim([sound.xmin, sound.xmax])
    plt.xlabel("time [s]")
    plt.ylabel("amplitude")
    waveform_path = os.path.join(image_folder, "waveform.png")
    plt.savefig(waveform_path)
    plt.close()

    # Spectrogram + intensity
    intensity = sound.to_intensity()
    spectrogram = sound.to_spectrogram()
    plt.figure()
    draw_spectrogram(spectrogram)
    plt.twinx()
    draw_intensity(intensity)
    plt.xlim([sound.xmin, sound.xmax])
    spectrogram_intensity_path = os.path.join(image_folder, "spectrogram_intensity.png")
    plt.savefig(spectrogram_intensity_path)
    plt.close()

    # Spectrogram + pitch
    pitch = sound.to_pitch()
    pre_emphasized_snd = sound.copy()
    pre_emphasized_snd.pre_emphasize()
    spectrogram = pre_emphasized_snd.to_spectrogram(window_length=0.03, maximum_frequency=8000)
    plt.figure()
    draw_spectrogram(spectrogram)
    plt.twinx()
    draw_pitch(pitch)
    plt.xlim([sound.xmin, sound.xmax])
    spectrogram_pitch_path = os.path.join(image_folder, "spectrogram_pitch.png")
    plt.savefig(spectrogram_pitch_path)
    plt.close()

# Generate PDF report
def generate_pdf_report(metrics, image_folder, pdf_folder, pdf_filename="report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Speech Analysis Report", ln=True, align="C")

    pdf.set_font("Arial", 'B', 12)
    pdf.ln(10)

    # Metrics
    pdf.set_font("Arial", '', 12)
    for metric, value in metrics.items():
        pdf.multi_cell(0, 10, f"{metric}: {value}")

    # Page break before graphs
    pdf.add_page()

    # Waveform Plot
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Waveform", ln=True, align="C")
    pdf.ln(10)
    pdf.image(os.path.join(image_folder, "waveform.png"), w=190)

    # New page for spectrogram and intensity
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Spectrogram and Intensity", ln=True, align="C")
    pdf.ln(10)
    pdf.image(os.path.join(image_folder, "spectrogram_intensity.png"), w=190)

    # New page for spectrogram and pitch
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Spectrogram and Pitch", ln=True, align="C")
    pdf.ln(10)
    pdf.image(os.path.join(image_folder, "spectrogram_pitch.png"), w=190)

    pdf_output_path = os.path.join(pdf_folder, pdf_filename)
    pdf.output(pdf_output_path)

def process_audio_file(audio_file_path):
    """
    Function to process the audio file: generate plots, report, and PDF.
    """
    print("Processing audio file:", audio_file_path)
    
    # Normalize the audio file path to handle Windows and Unix-style paths
    audio_file = os.path.normpath(audio_file_path)

    # Create parent folder
    parent_folder = "speech_analysis_output"
    os.makedirs(parent_folder, exist_ok=True)

    # Create subdirectories for images, reports, and PDFs
    image_folder = os.path.join(parent_folder, "report_images")
    report_folder = os.path.join(parent_folder, "text_reports")
    pdf_folder = os.path.join(parent_folder, "pdf_reports")
    
    os.makedirs(image_folder, exist_ok=True)
    os.makedirs(report_folder, exist_ok=True)
    os.makedirs(pdf_folder, exist_ok=True)

    # Generate plots and save them in the image folder
    generate_plots(audio_file, image_folder)
    
    # Dummy transcription and phoneme prediction
    transcription = ["k", "a", "t"]  # Correct transcription of "cat"
    phoneme_prediction = ["k", "a", "t"]  # Recognized phonemes from the audio

    # Generate and save the report with metrics
    report_filename = "speech_report.txt"
    metrics = generate_and_save_report(audio_file, transcription, phoneme_prediction, report_folder, report_filename)

    # Generate the PDF report and save it in the pdf folder
    pdf_filename = "report.pdf"
    generate_pdf_report(metrics, image_folder, pdf_folder, pdf_filename)

    # Print the metrics if available
    if metrics is not None:
        print(metrics)

# Main entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <audio_file_path>")
        sys.exit(1)

    # Get the audio file path from command-line arguments
    audio_file_path = sys.argv[1]

    # Call the function to process the audio file
    process_audio_file(audio_file_path)
