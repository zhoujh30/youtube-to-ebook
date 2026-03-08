"""
Part 4: Send Newsletter via Email
Sends the generated articles as a nicely formatted email newsletter with EPUB attachment.
"""

import os
import smtplib
import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv
from ebooklib import epub

# Load your credentials
load_dotenv()
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def create_epub(articles):
    """
    Create an EPUB ebook from the articles for reading on mobile devices.
    Returns the path to the generated EPUB file.
    """
    today = datetime.now().strftime("%B %d, %Y")
    filename = f"youtube_digest_{datetime.now().strftime('%Y%m%d')}.epub"
    filepath = os.path.join(os.path.dirname(__file__), filename)

    # Create the ebook
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f"youtube-digest-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    book.set_title(f"YouTube Digest - {today}")
    book.set_language("en")
    book.add_author("YouTube Newsletter Bot")

    # CSS for nice formatting on ebook readers
    style = """
    body {
        font-family: Georgia, serif;
        line-height: 1.6;
        padding: 1em;
    }
    h1 {
        font-size: 1.5em;
        margin-top: 1em;
        border-bottom: 1px solid #ccc;
        padding-bottom: 0.3em;
    }
    h2 {
        font-size: 1.3em;
        margin-top: 1em;
    }
    h3 {
        font-size: 1.1em;
    }
    .intro {
        background: #f5f5f5;
        padding: 1em;
        border-left: 3px solid #666;
        margin-bottom: 1.5em;
        font-size: 0.95em;
    }
    .watch-link {
        margin-top: 1.5em;
        padding: 0.5em;
        background: #f0f0f0;
        display: block;
    }
    """
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)

    chapters = []

    # Create a chapter for each article
    for i, article in enumerate(articles):
        # Convert markdown to HTML
        article_html = markdown.markdown(article['article'])

        chapter_content = f"""
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="style/nav.css"/>
        </head>
        <body>
            <div class="intro">
                <p><em>This article is based on the video "<strong>{article['title']}</strong>" from the YouTube channel <strong>{article['channel']}</strong>.</em></p>
            </div>
            {article_html}
            <p class="watch-link">Watch the original video: {article['url']}</p>
        </body>
        </html>
        """

        chapter = epub.EpubHtml(
            title=article['title'][:50],
            file_name=f"chapter_{i+1}.xhtml",
            lang="en"
        )
        chapter.content = chapter_content
        chapter.add_item(nav_css)

        book.add_item(chapter)
        chapters.append(chapter)

    # Create table of contents
    book.toc = tuple(chapters)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Set the reading order
    book.spine = ["nav"] + chapters

    # Write the EPUB file
    epub.write_epub(filepath, book)

    print(f"  ✓ Created EPUB: {filename}")
    return filepath


def extract_guests_from_title(title):
    """
    Try to extract guest name(s) from a podcast video title.
    Returns a string like "Rick Beato" or None.
    """
    import re
    # Pattern: "First Last: topic ..." or "First Last – topic"
    m = re.match(r'^([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\s*[:\-–]', title)
    if m:
        return m.group(1)
    # Pattern: "topic with First Last" or "feat. First Last"
    m = re.search(r'\b(?:with|ft\.?|feat\.?)\s+([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})', title)
    if m:
        return m.group(1)
    # Pattern: "topic – First Last" at end
    m = re.search(r'[–—]\s*([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\s*$', title)
    if m:
        return m.group(1)
    return None


def create_newsletter_html(articles):
    """
    Create a The Information-style newsletter.
    Light background, black text. Bold sentences stay black but heavier weight.
    """
    today = datetime.now().strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 20px;
    background: #fff;
    color: #292929;
    -webkit-font-smoothing: antialiased;
  }}
  .wrapper {{
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 24px;
  }}
  .header {{
    padding-bottom: 20px;
    border-bottom: 1px solid #e0e0e0;
    margin-bottom: 8px;
  }}
  .header-label {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 11px;
    letter-spacing: 1.5px;
    color: #aaa;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .header h1 {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0;
    color: #292929;
    margin-bottom: 6px;
  }}
  .header-date {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #aaa;
  }}
  .article {{
    padding: 40px 0;
    border-bottom: 1px solid #e8e8e8;
  }}
  .article-byline {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
    color: #757575;
    margin-bottom: 28px;
    line-height: 1.5;
  }}
  .article-byline .channel {{
    font-weight: 600;
    color: #292929;
  }}
  .article-content {{
    font-size: 20px;
    line-height: 1.8;
    color: #292929;
    letter-spacing: -0.003em;
  }}
  .article-content h1 {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 36px;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.5px;
    margin-bottom: 20px;
    color: #111;
  }}
  .article-content h2 {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 22px;
    font-weight: 700;
    margin: 36px 0 12px;
    color: #111;
  }}
  .article-content h3 {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    font-size: 18px;
    font-weight: 700;
    margin: 28px 0 10px;
    color: #111;
  }}
  .article-content p {{
    margin-bottom: 20px;
  }}
  .article-content strong {{
    font-weight: 700;
    color: #111;
  }}
  .article-content em {{
    font-style: italic;
  }}
  .article-content blockquote {{
    border-left: 3px solid #292929;
    margin: 24px 0;
    padding: 4px 0 4px 20px;
    color: #555;
    font-style: italic;
  }}
  .article-content a {{
    color: #292929;
    text-decoration: underline;
  }}
  .article-thumb {{
    width: 100%;
    max-height: 340px;
    object-fit: cover;
    display: block;
    margin-bottom: 24px;
    border-radius: 3px;
  }}
  .watch-link {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    display: inline-block;
    margin-top: 20px;
    font-size: 13px;
    font-weight: 600;
    color: #757575;
    text-decoration: none;
    border-bottom: 1px solid #ccc;
    padding-bottom: 2px;
    letter-spacing: 0.2px;
  }}
  .footer {{
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
    text-align: center;
    color: #ccc;
    font-size: 12px;
    padding: 32px 0 8px;
    letter-spacing: 0.5px;
  }}
  @media (max-width: 520px) {{
    .wrapper {{ padding: 24px 18px; }}
    .article-content {{ font-size: 18px; }}
    .article-content h1 {{ font-size: 28px; }}
    .article-content h2 {{ font-size: 20px; }}
  }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="header-label">Tech / AI</div>
    <h1>Daily Digest</h1>
    <div class="header-date">{today}</div>
  </div>
"""

    for article in articles:
        article_html = markdown.markdown(article['article'])
        guest = extract_guests_from_title(article['title'])
        if guest:
            authors = f"{article['channel']} &nbsp;·&nbsp; {guest}"
        else:
            authors = article['channel']
        video_id = article.get('video_id', '')
        thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

        html += f"""  <div class="article">
    <div class="article-byline">
      <span class="channel">{authors}</span>
    </div>
    {'<img src="' + thumb_url + '" alt="thumbnail" class="article-thumb">' if thumb_url else ''}
    <div class="article-content">
      {article_html}
    </div>
    <a href="{article['url']}" class="watch-link">Watch original &rarr;</a>
  </div>
"""

    html += """  <div class="footer">Daily Digest &mdash; Generated automatically</div>
</div>
</body>
</html>
"""
    return html


def save_newsletter_archive(html_content, epub_path, articles):
    """
    Save a copy of the newsletter for viewing in the archive.
    """
    newsletters_dir = os.path.join(os.path.dirname(__file__), "newsletters")
    os.makedirs(newsletters_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_display = datetime.now().strftime("%B %d, %Y")

    # Save HTML
    html_path = os.path.join(newsletters_dir, f"newsletter_{timestamp}.html")
    with open(html_path, "w") as f:
        f.write(html_content)

    # Copy EPUB
    import shutil
    epub_archive_path = os.path.join(newsletters_dir, f"newsletter_{timestamp}.epub")
    shutil.copy(epub_path, epub_archive_path)

    # Save metadata
    metadata = {
        "date": date_display,
        "timestamp": timestamp,
        "article_count": len(articles),
        "channels": [a["channel"] for a in articles],
        "titles": [a["title"] for a in articles],
        "html_file": f"newsletter_{timestamp}.html",
        "epub_file": f"newsletter_{timestamp}.epub"
    }

    metadata_path = os.path.join(newsletters_dir, f"newsletter_{timestamp}.json")
    import json
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  ✓ Saved newsletter to archive")


def send_newsletter(articles, recipient_email=None):
    """
    Send the newsletter via Gmail with EPUB attachment.
    If no recipient specified, sends to yourself.
    """
    if not articles:
        print("No articles to send!")
        return False

    # Default to sending to yourself
    if recipient_email is None:
        recipient_email = GMAIL_ADDRESS

    print(f"\nPreparing newsletter for {recipient_email}...")

    # Create EPUB ebook
    print("  Creating EPUB ebook...")
    epub_path = create_epub(articles)

    # Create the email (mixed type for attachments)
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Your YouTube Digest - {datetime.now().strftime('%B %d, %Y')}"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient_email

    # Create the body part (alternative for text/html)
    body = MIMEMultipart("alternative")

    # Create HTML content
    html_content = create_newsletter_html(articles)

    # Create plain text version (simple fallback)
    text_content = "Your YouTube Newsletter\n\n"
    text_content += "📚 EPUB ebook attached - open on your phone's ebook reader!\n\n"
    for article in articles:
        text_content += f"--- {article['channel']} ---\n"
        text_content += f"{article['article']}\n"
        text_content += f"Watch: {article['url']}\n\n"

    # Attach both text versions to body
    body.attach(MIMEText(text_content, "plain"))
    body.attach(MIMEText(html_content, "html"))

    # Add body to message
    msg.attach(body)

    # Attach EPUB file
    print("  Attaching EPUB file...")
    with open(epub_path, "rb") as attachment:
        part = MIMEBase("application", "epub+zip")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(epub_path)}"
        )
        msg.attach(part)

    try:
        # Connect to Gmail and send
        print("  Sending email...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient_email, msg.as_string())

        print("✓ Newsletter sent successfully with EPUB attachment!")

        # Save to archive before cleaning up
        save_newsletter_archive(html_content, epub_path, articles)

        # Clean up EPUB file
        os.remove(epub_path)

        return True

    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False


# Test it standalone
if __name__ == "__main__":
    # Test with mock articles
    test_articles = [
        {
            "title": "Test Article",
            "channel": "Test Channel",
            "url": "https://youtube.com/watch?v=test",
            "article": "# Test Headline\n\nThis is a test article with **bold** and *italic* text.\n\n## Section 1\n\nSome content here."
        }
    ]

    print("Sending test newsletter...")
    send_newsletter(test_articles)
