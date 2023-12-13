import requests
import json
import re
from serpapi import GoogleSearch
from bs4 import BeautifulSoup
import json
import os
import csv
import openai
from dotenv import load_dotenv

load_dotenv()
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()


def scrape():
    url = "https://www.gov.pl/web/poland-businessharbour-en/itspecialist"
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup)

    content = soup.select("#main-content")[0]
    details = content.find_all("details")
    company_contacts = []
    final_company_contacts = []

    for i,info in enumerate(details,1):
        # print(f"{i}. {info}")
        title = info.find("summary")
        # Using regular expression to find the email address
        for word in info.text:
                matches = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}\b', info.text)
                for match in matches:
                    if match == '\n':
                        pass
                    else:
                        Title = title.text.replace('\xa0', ' ')
                        company_info = {"company_name": Title, "company_email": match}
                        company_contacts.append(company_info)

    for contact in company_contacts:
        if contact in final_company_contacts:
            pass
        else:
            final_company_contacts.append(contact)
            print(f"Unique company entry: {contact}")
    return final_company_contacts


def company_search(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
    "q": query,
    "gl": "us",
    "num": 5,
    })
    headers = {
    'X-API-KEY': SERPAPI_API_KEY,
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response_data = response.json()
    return response_data


def homepage_scrape(url):
    try:
        response = requests.get(url, timeout=6)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.body
        if body:
            if len(body.text) > 2000 :
                page_content = body.text[0:2000]
                return page_content
            return body.text
        else:
            return f"No body found on the page- {url}"
    except Exception as e:
        print(e)
        return e
    

def prepare_summary(company_contacts):

    headers = ["company_name", "company_email", "company_summary"]
    with open("poland_job_application.csv", "w", newline='') as wb:
        writer = csv.writer(wb)
        writer.writerow(headers)
        
    for contact in company_contacts:
        company_name = contact["company_name"]
        company_email = contact["company_email"]

        search = company_search(company_name)
        url = search["organic"][0]["link"]
        print(url) 
        home = homepage_scrape(url)


        results = search["organic"]
        instruction = f"Using these google search results, summarize what technical works and skills the company does: {results}\n{home}"
        response = client.chat.completions.create(        
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{instruction}"}
        ],
            temperature=0.1,
            max_tokens=90,
            top_p=0,
            frequency_penalty=0 ,
            presence_penalty=0
        )
        content =  response.choices[0].message.content

        contact["company_summary"] = content
        print(contact)
        
        cell_content =[contact["company_name"], contact["company_email"], contact["company_summary"]] 
        with open("poland_job_application.csv", "a", encoding="utf-8", newline='') as wb:
            writer = csv.writer(wb)
            writer.writerow(cell_content)



if __name__ == '__main__':
    company_contacts = scrape()
    prepare_summary(company_contacts)


