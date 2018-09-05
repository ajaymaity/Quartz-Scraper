from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import os
import requests
import sys
import time

# Parse command line arguments
cmd_line_args = sys.argv
search_keyword = ""
if (len(cmd_line_args) < 2):
    print("Search Keyword is required to scrap Quartz.")
    print("Usage: python %s <search_keyword>" % (cmd_line_args[0]))
    print("Example: python %s flood" % (cmd_line_args[0]))
    sys.exit()
else:
    for idx, arg in enumerate(cmd_line_args):
        if idx == 0:
            continue
        search_keyword += "%s " % (arg)
search_keyword = search_keyword.strip()
URL = "https://qz.com/search/%s/" % (search_keyword)

# CHANGE THIS TO YOUR NEED
NO_OF_ARTICLES = 100
DELAY_BETWEEN_SCROLLS = 3 # in seconds

# Start driver
driver = webdriver.Chrome()
driver.get(URL)

# Scroll through the page multiple times to load the new articles
old_scroll_height = -1
while True:
    new_scroll_height = driver.execute_script("return document.body.scrollHeight")
    if (new_scroll_height == old_scroll_height):
        break
    old_scroll_height = new_scroll_height
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(DELAY_BETWEEN_SCROLLS)
    
    # Check how many articles we have
    main = driver.find_element(By.ID, "main")
    articles = main.find_elements(By.XPATH, "div[4]/div/div/div/article")
    if len(articles) >= NO_OF_ARTICLES:
        break

# Find the articles
main = driver.find_element(By.ID, "main")
articles = main.find_elements(By.XPATH, "div[4]/div/div/div/article")
article_url = list()
for idx, article in enumerate(articles):
    if idx >= NO_OF_ARTICLES:
        break
    article_url.append(article.find_element(By.XPATH, "div/a").get_attribute("href"))

driver.quit()

# article_url = ['https://qz.com/1260067/emmanuel-macron-gifted-donald-trump-a-bare-dead-looking-tree-and-first-lady-melania-trump-loves-it/'] # TESTING
# article_url = ['https://qz.com/543904/can-trees-really-change-sex/'] # TESTING
# article_url = ['https://qz.com/157109/latest-gizmo-to-join-internet-of-things-is-your-christmas-tree/']

num_articles = len(article_url)
print("Found %d number of articles." % (num_articles))

# Create a directory if not present
if not os.path.isdir("images"):
    os.makedirs("images")
# Delete content in the image directory
for file in os.listdir("images"):
    os.remove(os.path.join("images", file))

with open("scraped_news_content.csv", "w", encoding="utf-8", newline='') as scraped_news_file:
    with open("scraped_fig_for_news_content.csv", "w", encoding="utf-8", newline='') as scraped_fig_for_news_content_file:

        # Initialize CSV objects and define headers
        csv_writer_news = csv.writer(scraped_news_file, delimiter=",")
        csv_writer_news.writerow(["ArticleURL", "Tagline", "Heading", "Author", "Datetime", "Text", "Figures"])
        csv_writer_figs = csv.writer(scraped_fig_for_news_content_file, delimiter=",")
        csv_writer_figs.writerow(["FigureNo", "FigureURL", "FigureCaption"])

        # Scrap the data from web
        figure_no = 0
        for idx_url, url in enumerate(article_url):

            print("Scraping: %s" % (article_url[idx_url]))
            figure_links = list()
            figure_captions = list()

            page = requests.get(url)
            soup = BeautifulSoup(page.text, "html.parser")
            main = soup.find("div", {"id": "main"})
            article = main.find("article", recursive=False)
            header = article.find("header", recursive=False)            
            header_div = header.find("div", recursive=False)
            header_div_children = header_div.find_all(recursive=False)
            header_div_divs = header_div.select("div")
            header_fig = header.find("figure", recursive=False)
            heading = header_div.select("h1")[0].get_text()
            
            i = 0
            author_found = False
            datetime_found = False
            if len(header_div_divs) == 2: tagline = ""
            elif len(header_div_divs) == 4:
                if header_div_children[0].name == "h1":
                    tagline = ""
                    span_author_datetime = header_div.find("div", recursive=False).select("div")[2].find("span", recursive=False).select("span")
                    author = span_author_datetime[0].find("a", recursive=False).get_text()
                    author_found = True
                    datetime = span_author_datetime[2].find("time", recursive=False).get_text()
                    datetime_found = True
            else:
                tagline = header_div.select("div")[0].get_text()
                i = 1
            
            if not author_found:
                author = header_div_divs[i].select("div > span")[0].select("span")[0].select("a")[0].get_text()
            if not datetime_found:
                header_div_span = header_div_divs[i].select("div > span")[0].select("span")
                try:
                    if len(header_div_span) == 4:
                        datetime = header_div_span[3].select("time")[0].get_text()
                    else:
                        datetime = header_div_span[2].select("time")[0].get_text()
                except IndexError:
                    datetime = header_div.select("div")[1].select("div > span")[0].select("span")[3].select("time")[0].get_text()
            
            if header_fig is not None:
                try:
                    figure_captions.append(header_fig.find("figcaption", recursive=False).get_text())
                except AttributeError:
                    figure_captions.append("")
                figure_links.append(header_fig.find("div", recursive=False).select("div")[0].find("img")["src"].split("?", 1)[0])
            contents = article.find("div", recursive=False).find("div", recursive=False)
            text = contents.select("p")
            article_text = ""
            for paragraph in text:
                article_text += paragraph.get_text() + "\n"
            figures = contents.select("figure")
            for figure in figures:
                try:
                    figure_captions.append(figure.find("figcaption", recursive=False).get_text())
                except AttributeError:
                    figure_captions.append("")
                figure_links.append(figure.find("div", recursive=False).select("div")[0].find("img")["src"].split("?", 1)[0])

            if len(figure_links) > 0:
                if len(figure_links) == 1:
                    figure_no_text = "%d" % (figure_no + 1)
                else:
                    figure_no_text = "%d-%d" % (figure_no + 1, figure_no + len(figure_links))
            else:
                figure_no_text = ""
            
            # Write to CSV
            csv_writer_news.writerow([url, tagline, heading, author, datetime, article_text, figure_no_text])
            for idx_fig, figure_link in enumerate(figure_links):
                figure_no += 1
                figure_ext = figure_link.rsplit(".", 1)[-1]
                response = requests.get(figure_link)
                if response.status_code == 200:
                    with open("images/%d.%s" % (figure_no, figure_ext), "wb") as image_file:
                        image_file.write(response.content)
                csv_writer_figs.writerow([figure_no, figure_link, figure_captions[idx_fig]])

            print("Scraped %d article of %d." % (idx_url + 1, num_articles))
