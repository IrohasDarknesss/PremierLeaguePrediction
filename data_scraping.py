import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import time

def fetch_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data from {url}, Status code: {response.status_code}")
        return None
    return response.text

def extract_team_data(url):
    html_data = fetch_data(url)
    if html_data is None:
        return []

    soup = bs(html_data, 'lxml')
    table = soup.select_one('table.stats_table')
    if not table:
        print("No 'stats_table' found on the page.")
        return []

    team_links = [link.get("href") for link in table.find_all('a') if '/squads/' in link.get("href")]
    team_urls = [f"https://fbref.com{link}" for link in team_links]
    return team_urls

def main():
    url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    team_urls = extract_team_data(url)
    all_matches = []

    for team_url in team_urls:
        team_data = fetch_data(team_url)
        if team_data is None:
            continue

        matches = pd.read_html(team_data, match="Scores & Fixtures")[0]
        soup = bs(team_data, 'lxml')
        shooting_link = next((link.get("href") for link in soup.find_all('a') if 'all_comps/shooting/' in link), None)
        
        if shooting_link:
            shooting_data = fetch_data(f"https://fbref.com{shooting_link}")
            if shooting_data:
                shooting = pd.read_html(shooting_data, match="Shooting")[0]
                shooting.columns = shooting.columns.droplevel()
                matches = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
                all_matches.append(matches)
        
        time.sleep(20)  # Prevent hitting rate limits

    if all_matches:
        match_df = pd.concat(all_matches)
        match_df.columns = [c.lower() for c in match_df.columns]
        match_df.to_csv("./dataset/matches.csv")

if __name__ == "__main__":
    main()
