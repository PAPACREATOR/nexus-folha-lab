"""Local-only, non-executing language experiment. Never calls the Nexus Host."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json
from nexus.frontdoor import parse, parse_with_languagetool
from folha_lab.local_ai import suggest_question
from folha_lab.local_language import local_diagnostic
import hashlib

PAGE = (Path(__file__).parent / "index.html").read_bytes()
class Handler(BaseHTTPRequestHandler):
    def _trusted_browser(self):
        """Refuse foreign Host/Origin before invoking language or local services."""
        address = "127.0.0.1:" + str(self.server.server_port)
        if self.headers.get("Host") != address:
            self.send_error(403, "Unexpected local host")
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != "http://" + address:
            self.send_error(403, "Unexpected browser origin")
            return False
        return True

    def do_GET(self):
        if not self._trusted_browser(): return
        if urlsplit(self.path).path != "/": return self.send_error(404)
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(PAGE)
    def do_POST(self):
        if not self._trusted_browser(): return
        if self.path != "/interpret": return self.send_error(404)
        if self.headers.get("Content-Type","").split(";")[0].strip() != "application/json": return self.send_error(415)
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n < 1 or n > 250000: return self.send_error(413)
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict) or set(data)-{"text","languagetool"} or not isinstance(data.get("text"),str): return self.send_error(400)
            text = data["text"]
            if "languagetool" in data:
                parsed = parse_with_languagetool(text, data["languagetool"])
            else:
                parsed = parse(text)
                if parsed.status == "UNRESOLVED" and not parsed.explicit:
                    # Optional local-only LanguageTool before optional local AI.
                    diagnostic = local_diagnostic(text)
                    if diagnostic is not None:
                        parsed = parse_with_languagetool(text, diagnostic)
            result = parsed.as_dict()
            result["execution"]="SIMULATED_ONLY"
            if result["status"]=="RESOLVED":
                result["confirmation_required"]=True
                result["proposal_id"]=hashlib.sha256((result["original"]+"\\0"+result["intent"]).encode("utf-8")).hexdigest()
                result["question"]="Interpretaste corretamente o pedido? Confirmas esta proposta? (Nenhuma ação será executada neste laboratório.)"
            else:
                result["confirmation_required"]=False
            if result["status"]=="UNRESOLVED":
                fallback = "Podes explicar com outras palavras o que pretendes fazer?"
                # Only unresolved natural language may consult the optional local model.
                ai_question = None if result["explicit"] else suggest_question(result["original"])
                result["question"] = ai_question or fallback
                result["question_source"] = "local_model" if ai_question else "deterministic"
            if result["status"]=="BLOCKED":
                result["question"] = "O pedido contém dados inválidos ou ultrapassa o limite permitido."
            body=json.dumps(result,ensure_ascii=False).encode("utf-8")
        except (ValueError,TypeError,UnicodeError,KeyError): return self.send_error(400)
        self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
if __name__=="__main__":
    print("Folha Lab (simulação): http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
