import os # Para interactuar con el sistema operativo, como crear directorios y listar archivos
import shutil # (Shell Utility) se usa para operaciones de alto nivel en archivos, como copiar archivos de un lugar a otro
from pydub import AudioSegment # Para representar y manipular clips de audio
from pydub.silence import detect_silence #  Para detectar secciones de silencio en un clip de audio
# VideoFileClip - para representar y manipular clips de video
# AudioFileClip - para representar y manipular clips de audio.
# concatenate_videoclips - para concatenar varios clips de video en uno solo
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# -------------------------------------------------------------------------------------------------------------------------------------
def export_audio_to_create_audio_moviepy(audio, temp_audio_path, format):
    audio.export(temp_audio_path, format)
    final_audio_moviepy = AudioFileClip(temp_audio_path)
    return final_audio_moviepy
# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
def extract_non_silent_segments_audio_video_from_silent_sections(video, audio, silent_sections, start_time=0, margin_ms=0):
    non_silent_video_segments_margin = []
    non_silent_audio_segments_margin = []
    
    print("🧩 Extracting non-silent segments...")

    for silent_start, silent_end in silent_sections:
        # Retrocedemos 'margin_ms' milisegundos para dejar el margen al comienzo
        start_time_with_margin = max(0, start_time - margin_ms)
        end_time_with_margin = silent_start + margin_ms
        
        non_silent_video_segments_margin.append(video.subclip(start_time_with_margin / 1000, end_time_with_margin / 1000))
        non_silent_audio_segments_margin.append(audio[start_time_with_margin:end_time_with_margin])

        start_time = silent_end

    end_time = len(audio)
    start_time_with_margin = max(0, start_time - margin_ms) # Aquí también aplicamos el margen para el último segmento
    non_silent_video_segments_margin.append(video.subclip(start_time_with_margin / 1000, end_time / 1000))
    non_silent_audio_segments_margin.append(audio[start_time_with_margin:end_time])

    return {
        'video_segments': non_silent_video_segments_margin,
        'audio_segments': non_silent_audio_segments_margin
    }
# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
def convert_video_with_non_silent_sections(input_video_path, start_time, margin_ms, decibels, milliseconds, output_directory, temp_folder):
    try:
        video = VideoFileClip(input_video_path)
        print("📹 Video successfully imported")
        audio = AudioSegment.from_file(input_video_path)
        print("🔊 Audio successfully imported")
    except Exception as e:
        print(f"😥 Error: {e}")
        return  # Retorna temprano en caso de error
    
    print("🤔 Detecting silent segments...")

    silent_sections = detect_silence(audio, silence_thresh=decibels, min_silence_len=milliseconds)
    non_silent_segments_video_audio = extract_non_silent_segments_audio_video_from_silent_sections(video, audio, silent_sections, start_time, margin_ms)
    print("🧵 Joining non-silent video and audio segments...")
    final_video = concatenate_videoclips(non_silent_segments_video_audio['video_segments'])
    print("📹 Video successfully joined")
    final_audio = sum(non_silent_segments_video_audio['audio_segments'])
    print("🔊 Audio successfully joined")

    final_audio_moviepy = export_audio_to_create_audio_moviepy(final_audio, "./" + temp_folder + "/temp_audio.wav", "wav")

    final_video.audio = final_audio_moviepy

    output_video_path = os.path.join(output_directory, os.path.basename(input_video_path))  # Usa el mismo nombre de archivo, pero en el directorio de salida
    final_video.write_videofile(output_video_path, codec="libx264")

    video.close()
    final_audio_moviepy.close()
# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
def copy_video_to_temp_folder(input_video_path, temp_folder):
    if not os.path.exists(temp_folder):
        print(f"📁 Creating temporary folder... '{temp_folder}'")
        os.makedirs(temp_folder)  # Crea la carpeta si no existe

    dest_path = os.path.join(temp_folder, os.path.basename(input_video_path))
    print(f"💞 Copying video... '{input_video_path}'")
    shutil.copy(input_video_path, dest_path)  # Copia el archivo

    return dest_path  # Devuelve la ruta de la copia
# -------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------
def process_all_videos_in_directory(input_directory, output_directory, start_time, margin_ms, silence_thresh, min_silence_len):
    # Crea el directorio de salida si no existe
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    temp_folder = "temp"  # Carpeta temporal donde se almacenarán las copias

    # Itera sobre todos los archivos en el directorio de entrada
    for filename in os.listdir(input_directory):
        if filename.endswith(".mp4"):
            input_video_path = os.path.join(input_directory, filename)
            
            # Crea una copia del archivo en la carpeta temporal
            temp_video_path = copy_video_to_temp_folder(input_video_path, temp_folder)
            print(f"😁 Video '{input_video_path}' successfully copied")
            # Procesa la copia del archivo
            convert_video_with_non_silent_sections(temp_video_path, start_time, margin_ms, silence_thresh, min_silence_len, output_directory, temp_folder)

# -------------------------------------------------------------------------------------------------------------------------------------

# Parámetros
input_directory = "."  # Directorio actual, ajusta esto a tu directorio de entrada
output_directory = "output_videos"
start_time = 0
margin_ms = 200
silence_thresh = -45
min_silence_len = 800

# Procesa todos los videos
process_all_videos_in_directory(input_directory, output_directory, start_time, margin_ms, silence_thresh, min_silence_len)