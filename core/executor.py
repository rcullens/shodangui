import subprocess
import ollama

class ExploitExecutor:
    @staticmethod
    def run_sqlmap(target_url: str) -> str:
        try:
            cmd = ["sqlmap", "-u", target_url, "--batch", "--banner", "--random-agent", "--level=1", "--risk=1"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return result.stdout if result.stdout else result.stderr
        except FileNotFoundError:
            return "[!] ERROR: 'sqlmap' is not installed or not in system PATH."
        except subprocess.TimeoutExpired:
            return "[!] ERROR: sqlmap execution timed out (120s)."
        except Exception as e:
            return f"[!] ERROR: {str(e)}"

    @staticmethod
    def generate_msf_playbook(target_info: dict, model_name: str = "llama3.2") -> str:
        system_prompt = (
            "You are an expert red-teaming instructor and Metasploit Framework specialist. "
            "Given target telemetry (IP, port, title, banner, CVEs), write a comprehensive, step-by-step operator playbook "
            "for attacking this specific target in msfconsole. "
            "CRITICAL: Only reference real, verified Metasploit module paths that exist within the standard framework repository "
            "(e.g., auxiliary/scanner/http/..., exploit/multi/http/..., exploit/unix/webapp/...). Never invent or hallucinate module names. "
            "Include: "
            "1. Recommended exploit or auxiliary module path. "
            "2. Optimal payload selection with reasoning. "
            "3. Exact configuration commands (e.g., set RHOSTS, set RPORT, set LHOST). "
            "4. Post-exploitation or verification steps. "
            "Format the output clearly with headings and exact code blocks for console entry."
        )
        user_prompt = f"Target Telemetry:\n{target_info}"
        try:
            response = ollama.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.get('message', {}).get('content', '').strip()
        except Exception as e:
            return f"[!] Error generating AI playbook: {str(e)}"
