import os
import feedparser
from openai import OpenAI
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, body):
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    receiver = os.getenv("RECIEVER_EMAIL")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    part = MIMEText(body, "plain")
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
            print("✅ Email sent!")
    except Exception as e:
        print(f"❌ Email failed: {e}")


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -- RSS FEEDS --
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "AWS": "https://aws.amazon.com/blogs/aws/feed/",
    "Cloudflare": "https://blog.cloudflare.com/rss/",
    "Duolingo": "https://blog.duolingo.com/rss/"
}

# -- Fetch articles from multiple feeds --
def fetch_articles(feeds, limit=5):
    all_articles = []

    for source, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            article = {
                "source": source,
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if "summary" in entry else "",
                "published": entry.published if "published" in entry else ""
            }
            all_articles.append(article)

    return all_articles

# -- Ask OpenAI to pick top 3 based on your interests --
def pick_top_articles(articles):
    prompt = (
        "You are a personal content assistant helping Yusuf pick the 3 most interesting blog posts from a list.\n"
        "He likes articles about cloud trends, developer productivity, startup culture, privacy issues, "
        "and applications of AI. He’s concerned about tracking, unethical use of AI, and bloated tools.\n\n"
        "Pick the top 3 that align most with those interests. Return a short summary, title, and link for each of the three.\n\n"
        f"Here is the list of articles:\n\n"
    )

    for a in articles:
        prompt += f"Title: {a['title']}\nSource: {a['source']}\nLink: {a['link']}\nSummary: {a['summary']}\n\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You summarize and filter blog articles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    articles = fetch_articles(RSS_FEEDS, limit=5)
    top_summaries = pick_top_articles(articles)

    subject = "🧠 Your SummarAIze Daily Digest"
    send_email(subject, top_summaries)
    # send_email(subject, "Hello, this is a test email from SummarAIze. Please check your inbox for the latest updates.")