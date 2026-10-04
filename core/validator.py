import shodan
import time

class ShodanValidator:
    def __init__(self, api_key: str):
        self.api = shodan.Shodan(api_key)
        self.honeypot_indicators = [
            "honeypot", "cowrie", "dionaea", "default page", 
            "test page", "internal server error", "403 forbidden",
            "unauthorized", "login required"
        ]

    def _is_vulnerable_or_exposed(self, banner_data: dict) -> bool:
        banner_text = str(banner_data.get('data', '')).lower()
        title = str(banner_data.get('http', {}).get('title', '')).lower()
        html = str(banner_data.get('http', {}).get('html', '')).lower()
        vulns = banner_data.get('vulns', [])
        
        combined = f"{banner_text} {title} {html}"
        
        for indicator in self.honeypot_indicators:
            if indicator in combined:
                return False
                
        if len(banner_text.strip()) < 10:
            return False
            
        has_cve = len(vulns) > 0
        has_exposure_indicators = any(term in combined for term in [
            "admin", "dashboard", "setup", "config", "camera", "stream", 
            "pos", "terminal", "root", "debug", "open", "index of", "sql", "syntax"
        ])
        
        return has_cve or has_exposure_indicators

    def test_dork(self, query: str) -> list:
        valid_hits = []
        try:
            results = self.api.search(query, limit=10)
            for match in results.get('matches', []):
                if self._is_vulnerable_or_exposed(match):
                    valid_hits.append({
                        'ip': match.get('ip_str'),
                        'port': match.get('port'),
                        'org': match.get('org', 'Unknown'),
                        'location': match.get('location', {}).get('country_name', 'Unknown'),
                        'title': match.get('http', {}).get('title', 'N/A'),
                        'vulns': list(match.get('vulns', [])),
                        'banner': match.get('data', '')[:200]
                    })
            time.sleep(0.5)
        except Exception:
            pass
        return valid_hits
