import ollama
import re

class AIDorkGenerator:
    def __init__(self, model_name: str = "llama3.2"):
        self.model = model_name

    def generate_dorks(self, keyword: str, category: str = "general") -> list:
        system_prompt = (
            "You are an expert security researcher and Shodan dork engineer. "
            "Your job is to take abstract or complex keywords (like software names, hardware types, or industrial systems) "
            "and translate them into valid, working Shodan search queries using proper filters like "
            "http.title, html, product, version, port, http.component, or ssl.cert.subject.cn. "
            "Never output plain text that won't match anything. Every query must be syntactically valid for Shodan. "
            "Output ONLY the raw dorks, one per line, with no extra text or numbering."
        )
        
        if category == "sql":
            user_prompt = (
                f"Generate 10 advanced Shodan dorks targeting potential SQL injection points, database management panels, "
                f"or exposed database ports related to this keyword/application: '{keyword}'. "
                f"Incorporate filters like http.title, html error strings, or database ports (3306, 1433, 5432)."
            )
        else:
            user_prompt = (
                f"Generate 12 high-precision, non-public Shodan dorks to discover instances, panels, or devices "
                f"related to this keyword: '{keyword}'. Ensure they use valid Shodan syntax and operators."
            )

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.get('message', {}).get('content', '')
            dorks = [line.strip() for line in content.split('\n') if line.strip()]
            cleaned_dorks = []
            for d in dorks:
                d_clean = re.sub(r'^[0-9]+\.\s*|^\-\s*|^`+|`+$', '', d).strip()
                if d_clean:
                    cleaned_dorks.append(d_clean)
            return cleaned_dorks[:12] if cleaned_dorks else self._fallback_dorks(keyword, category)
        except Exception as e:
            print(f"[!] Ollama generation failed ({e}). Falling back to heuristic engine.")
            return self._fallback_dorks(keyword, category)

    def _fallback_dorks(self, keyword: str, category: str) -> list:
        kw = keyword.lower().strip()
        if category == "sql":
            return [
                f'{kw} http.title:"sql syntax"',
                f'{kw} html:"sql syntax near"',
                f'{kw} html:"warning: mysql"',
                f'{kw} port:3306 product:mysql',
                f'{kw} port:1433 product:"microsoft sql server"'
            ]
        else:
            return [
                f'http.title:"{kw}"',
                f'html:"{kw}"',
                f'product:"{kw}"',
                f'http.component:"{kw}"'
            ]
