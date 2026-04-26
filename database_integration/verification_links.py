"""
Live Legal Database Verification Links
========================================
Auto-generates verification URLs for Indian Kanoon, Casemine, and PRS India
so judges can one-click verify any citation in the AI's reasoning.
"""

import urllib.parse
from typing import List, Dict


class IndianKanoonIntegration:
    """Generate search links for Indian Kanoon (80M+ judgments)."""
    BASE = "https://indiankanoon.org/search/?formInput="

    def search_url(self, query: str) -> str:
        return self.BASE + urllib.parse.quote(query + " India")

    def case_url(self, case_name: str) -> str:
        return self.BASE + urllib.parse.quote(f'"{case_name}"')


class CasemineIntegration:
    """Generate search links for Casemine legal research."""
    BASE = "https://www.casemine.com/search#query="

    def search_url(self, query: str) -> str:
        return self.BASE + urllib.parse.quote(query)


class PRSIndiaIntegration:
    """Generate search links for PRS India legislative tracking."""
    BASE = "https://prsindia.org/billtrack?q="

    def search_url(self, query: str) -> str:
        return self.BASE + urllib.parse.quote(query)


class LiveVerificationLinksGenerator:
    """
    Generates one-click verification links for all citations in a verdict.
    Used by the UI to display "Verify on Indian Kanoon" buttons.
    """

    def __init__(self):
        self.ikanoon = IndianKanoonIntegration()
        self.casemine = CasemineIntegration()
        self.prs = PRSIndiaIntegration()

    def generate_links_for_verdict(
        self,
        reasoning_text: str,
        cited_authorities: List[str] = None,
        applicable_statutes: List[str] = None,
    ) -> Dict:
        """Generate verification links for a verdict's citations."""
        cited_authorities = cited_authorities or []
        applicable_statutes = applicable_statutes or []

        case_links = []
        for case in cited_authorities:
            case_links.append({
                "case": case,
                "indian_kanoon": self.ikanoon.case_url(case),
                "casemine": self.casemine.search_url(case),
            })

        statute_links = []
        for statute in applicable_statutes:
            statute_links.append({
                "statute": statute,
                "indian_kanoon": self.ikanoon.search_url(statute),
                "prs_india": self.prs.search_url(statute),
            })

        # General case search link
        snippet = reasoning_text[:80].strip() if reasoning_text else ""
        general_link = self.ikanoon.search_url(snippet)

        return {
            "case_links": case_links,
            "statute_links": statute_links,
            "general_search": general_link,
            "total_links": len(case_links) + len(statute_links) + 1,
        }

    def generate_html_report(self, links: Dict) -> str:
        """Generate an HTML snippet with clickable verification links."""
        html = '<div class="verification-links">\n'
        html += '<h4>🔍 Verify Citations</h4>\n'

        for cl in links.get("case_links", []):
            html += f'<p><strong>{cl["case"]}</strong>: '
            html += f'<a href="{cl["indian_kanoon"]}" target="_blank">Indian Kanoon</a> | '
            html += f'<a href="{cl["casemine"]}" target="_blank">Casemine</a></p>\n'

        for sl in links.get("statute_links", []):
            html += f'<p><strong>{sl["statute"]}</strong>: '
            html += f'<a href="{sl["indian_kanoon"]}" target="_blank">Indian Kanoon</a> | '
            html += f'<a href="{sl["prs_india"]}" target="_blank">PRS India</a></p>\n'

        html += '</div>'
        return html
