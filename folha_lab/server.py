"""Local-only, non-executing language experiment. Never calls the Nexus Host."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json
from nexus.frontdoor import parse, parse_with_languagetool

PAGE = (Path(__file__).parent / "index.html").read_bytes()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path != "/": return self.send_error(404)
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(PAGE)
    def do_POST(self):
        if self.path != "/interpret": return self.send_error(404)
        if self.headers.get("Content-Type","").split(";")[0].strip() != "application/json": return self.send_error(415)
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n < 1 or n > 250000: return self.send_error(413)
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict) or set(data)-{"text","languagetool"} or not isinstance(data.get("text"),str): return self.send_error(400)
            result=(parse_with_languagetool(data["text"],data["languagetool"]) if "languagetool" in data else parse(data["text"])).as_dict()
            result["execution"]="SIMULATED_ONLY"
            if result["status"]=="UNRESOLVED": result["question"]="Podes explicar com outras palavras o que pretendes fazer?"
            body=json.dumps(result,ensure_ascii=False).encode("utf-8")
        except (ValueError,TypeError,UnicodeError,KeyError): return self.send_error(400)
        self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
if __name__=="__main__":
    print("Folha Lab (simulação): http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
