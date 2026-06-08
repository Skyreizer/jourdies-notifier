#!/usr/bin/env python3
"""
Haute-Savoie Administrative Acts Monitor
Scrapes new documents and searches for specific terms, sending email notifications.
"""

import json
import re
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pdfplumber


class ActsMonitor:
    """Monitor for Haute-Savoie administrative acts."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the monitor with configuration."""
        self.config = self._load_config(config_path)
        self.state_file = Path(self.config.get("state_file", "state.json"))
        self.state = self._load_state()
        self.base_url = "https://www.haute-savoie.gouv.fr"
        self.acts_url = (
            f"{self.base_url}/Publications/Actes-administratifs/{self.config['year']}"
        )

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Config file '{config_path}' not found.")
            sys.exit(1)

    def _load_state(self) -> dict:
        """Load state from JSON file or create new state."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"last_check": None, "processed_docs": [], "matches_found": []}

    def _save_state(self):
        """Save current state to JSON file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def scrape_documents(self) -> List[Dict]:
        """
        Scrape documents from the acts page.
        Returns list of documents with metadata.
        """
        documents = []

        # Scrape first page and pagination info
        page_num = 0
        max_pages = self.config.get("max_pages_to_check", 3)  # Limit pages to check

        while page_num < max_pages:
            offset = page_num * 10
            url = f"{self.acts_url}/(offset)/{offset}" if offset > 0 else self.acts_url

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")

                # Find all document links
                page_docs = self._parse_page(soup)

                if not page_docs:
                    break  # No more documents

                documents.extend(page_docs)
                page_num += 1

            except requests.RequestException as e:
                print(f"Error fetching page {page_num}: {e}")
                break

        return documents

    def _parse_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse a single page and extract document information."""
        documents = []

        # Find all links to PDF documents
        for link in soup.find_all(
            "a", href=re.compile(r"/contenu/telechargement/.*\.pdf")
        ):
            doc_url = urljoin(self.base_url, link["href"])

            # Extract document ID from URL
            match = re.search(r"/telechargement/(\d+)/", doc_url)
            if not match:
                continue

            doc_id = match.group(1)

            # Skip if already processed
            if doc_id in self.state["processed_docs"]:
                continue

            # Get document title
            title = link.get_text(strip=True)

            # Try to find publication date (in nearby text)
            pub_date = None
            parent = link.find_parent()
            if parent:
                date_text = parent.get_text()
                date_match = re.search(r"Publié le (\d{2}/\d{2}/\d{4})", date_text)
                if date_match:
                    pub_date = date_match.group(1)

            documents.append(
                {
                    "id": doc_id,
                    "title": title,
                    "url": doc_url,
                    "publication_date": pub_date,
                }
            )

        return documents

    def download_and_parse_pdf(self, url: str) -> str:
        """Download a PDF and extract its text content."""
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            # Save temporarily
            temp_pdf = Path("/tmp/temp_doc.pdf")
            temp_pdf.write_bytes(response.content)

            # Extract text
            text = ""
            with pdfplumber.open(temp_pdf) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # Cleanup
            temp_pdf.unlink()

            return text

        except Exception as e:
            print(f"Error processing PDF {url}: {e}")
            return ""

    def search_in_text(self, text: str, search_terms: List[str]) -> List[str]:
        """
        Search for terms in text (case-insensitive).
        Returns list of found terms.
        """
        found_terms = []
        text_lower = text.lower()

        for term in search_terms:
            # Use word boundary search for more accurate matching
            pattern = r"\b" + re.escape(term.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found_terms.append(term)

        return found_terms

    def send_email_notification(self, matches: List[Dict]):
        """Send email notification about matches found."""
        if not matches:
            return

        smtp_config = self.config["email"]

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔔 {len(matches)} match(es) found in Haute-Savoie Acts"
        msg["From"] = smtp_config["from"]
        msg["To"] = smtp_config["to"]

        # Create email body
        text_body = self._create_text_email(matches)
        html_body = self._create_html_email(matches)

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send email
        try:
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
                server.starttls()
                if smtp_config.get("username") and smtp_config.get("password"):
                    server.login(smtp_config["username"], smtp_config["password"])
                server.send_message(msg)
            print(f"✓ Email notification sent to {smtp_config['to']}")
        except Exception as e:
            print(f"✗ Error sending email: {e}")

    def _create_text_email(self, matches: List[Dict]) -> str:
        """Create plain text email body."""
        body = f"Found {len(matches)} document(s) matching your search criteria:\n\n"

        for match in matches:
            body += f"Document: {match['title']}\n"
            body += f"URL: {match['url']}\n"
            body += f"Publication Date: {match['publication_date'] or 'Unknown'}\n"
            body += f"Terms found: {', '.join(match['found_terms'])}\n"
            body += "-" * 70 + "\n\n"

        body += f"\nChecked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        return body

    def _create_html_email(self, matches: List[Dict]) -> str:
        """Create HTML email body."""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .document { background-color: #f5f5f5; padding: 15px; margin: 15px 0; border-left: 4px solid #2196F3; }
                .title { font-weight: bold; font-size: 16px; margin-bottom: 8px; }
                .meta { color: #666; font-size: 14px; }
                .terms { color: #d32f2f; font-weight: bold; }
                a { color: #2196F3; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h2>🔔 Administrative Acts Monitor Alert</h2>
            <p>Found <strong>{count}</strong> document(s) matching your search criteria:</p>
        """.format(count=len(matches))

        for match in matches:
            html += f"""
            <div class="document">
                <div class="title">{match['title']}</div>
                <div class="meta">
                    📅 Published: {match['publication_date'] or 'Unknown'}<br>
                    <a href="{match['url']}" target="_blank">📄 View Document</a>
                </div>
                <div class="terms">
                    Terms found: {', '.join(match['found_terms'])}
                </div>
            </div>
            """

        html += f"""
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        return html

    def run(self):
        """Main execution method."""
        print(f"🔍 Starting Haute-Savoie Acts Monitor - {datetime.now()}")
        print(f"   Searching for: {', '.join(self.config['search_terms'])}")

        # Scrape documents
        print("📥 Scraping documents...")
        documents = self.scrape_documents()
        new_docs = [d for d in documents if d["id"] not in self.state["processed_docs"]]

        print(f"   Found {len(new_docs)} new document(s) to check")

        if not new_docs:
            print("✓ No new documents to process")
            self.state["last_check"] = datetime.now().isoformat()
            self._save_state()
            return

        # Process each new document
        matches = []
        for i, doc in enumerate(new_docs, 1):
            print(f"   [{i}/{len(new_docs)}] Processing: {doc['title']}")

            # Download and parse PDF
            text = self.download_and_parse_pdf(doc["url"])

            if text:
                # Search for terms
                found_terms = self.search_in_text(text, self.config["search_terms"])

                if found_terms:
                    print(f"      ✓ MATCH! Found: {', '.join(found_terms)}")
                    doc["found_terms"] = found_terms
                    matches.append(doc)
                    self.state["matches_found"].append(
                        {**doc, "found_at": datetime.now().isoformat()}
                    )

            # Mark as processed
            self.state["processed_docs"].append(doc["id"])

        # Send notification if matches found
        if matches:
            print(f"\n📧 Sending notification for {len(matches)} match(es)...")
            self.send_email_notification(matches)
        else:
            print("✓ No matches found in new documents")

        # Update state
        self.state["last_check"] = datetime.now().isoformat()
        self._save_state()

        print(f"✓ Monitor completed - {datetime.now()}")


def main():
    """Entry point for the script."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"

    try:
        monitor = ActsMonitor(config_file)
        monitor.run()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
