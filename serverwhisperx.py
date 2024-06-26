# Copyright (c) 2023 Braedon Hendy
# This software is released under the GNU General Public License v3.0

from http.server import BaseHTTPRequestHandler, HTTPServer
import whisperx
import cgi
import json
import os
import tempfile

# Initialize Whisper model
model_size = "medium.en"

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/whisperaudio':
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            if ctype == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                fields = cgi.parse_multipart(self.rfile, pdict)
                audio_data = fields.get('audio')[0]

                # Save the audio file temporarily
                with tempfile.NamedTemporaryFile(delete=False) as temp_audio_file:
                    temp_audio_file.write(audio_data)
                    temp_file_path = temp_audio_file.name

                try:
                    # Process the file with Whisper
                    model = whisperx.load_model(model_size, device="cuda", compute_type="float16")
                    audio = whisperx.load_audio(temp_file_path)
                    result = model.transcribe(audio)
                    text_segments = [segment['text'] for segment in result['segments']]                    
                    transcription = " ".join(text_segments)

                    # Send response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response_data = json.dumps({"text": transcription})
                    self.wfile.write(response_data.encode())
                finally:
                    # Clean up the temporary file
                    os.remove(temp_file_path)
            else:
                self.send_error(400, "Invalid content type")
        else:
            self.send_error(404, "File not found")

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Server running at http://localhost:{port}/')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
