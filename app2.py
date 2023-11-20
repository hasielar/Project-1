import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt

# Function to clean salary strings and calculate average salary
def clean_salary(salary):
    salary_values = re.findall(r'[\d,]+', salary)
    cleaned_salaries = [int(value.replace(',', '')) for value in salary_values]
    return sum(cleaned_salaries) / len(cleaned_salaries) if cleaned_salaries else None

# Function to scrape job postings
def scrape_job_postings(n_pages):
    job_titles = []
    job_salaries = []
    job_descriptions = []
    job_sectors = []

    try:
        for i in range(1, n_pages + 1):
            link = f"https://www.zangia.mn/job/list/pg.{i}"
            hp_response = requests.get(link)
            hp_soup = BeautifulSoup(hp_response.content, 'html.parser')
            ads = hp_soup.find_all("div", {"class": "ad"})
            urls = ["https://www.zangia.mn/" + ad.find('a').get('href') for ad in ads]

            for url in urls:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                page_content = soup.find_all("div", {"class": "job-body"})

                job_title = page_content[0].find("h3").get_text() if page_content[0].find("h3") else 'N/A'
                job_titles.append(job_title)

                job_description = page_content[0].find("ul").get_text() if page_content[0].find("ul") else 'N/A'
                job_descriptions.append(job_description)

                job_salary = page_content[0].find("div", {"class": "salary"}).get_text() if page_content[0].find("div", {"class": "salary"}) else 'N/A'
                job_salaries.append(job_salary)

                job_sector = page_content[0].find("div", {"class": "details"}).find_all('span')[1].get_text() if page_content[0].find("div", {"class": "details"}) else 'N/A'
                job_sectors.append(job_sector)

        job_postings_df = pd.DataFrame({
            "job_title": job_titles,
            "job_salary": job_salaries,
            "job_sector": job_sectors,
            "job_description": job_descriptions
        })

        job_postings_df['job_salary'] = job_postings_df['job_salary'].apply(clean_salary)

        return job_postings_df

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return pd.DataFrame()

def format_salary_value(salary):
    if salary >= 1_000_000:
        return f'{salary / 1_000_000:.1f} mil'
    elif salary >= 1_000:
        return f'{salary / 1_000:.1f} k'
    else:
        return f'{salary}'

# Streamlit app
def main():
    st.title('Mongolian Job Postings Analysis')

    st.markdown(
        """
        Welcome to the Mongolian Job Postings Analysis App! 🚀

        This app scrapes job postings data from a specific website in Mongolia and provides an analysis of the data.
        
        **How to Use:**
        - Adjust the slider to select the number of pages to scrape.
        - Click the 'Scrape' button to retrieve job postings data.
        
        **What You'll Get:**
        - Visualizations: Salary distribution pie chart, top 5 highest paying jobs, top 5 lowest paying jobs.
        - Information on the job with the longest title.
        """
    )

    n_pages = st.slider("Select number of pages to scrape:", 1, 10)

    if st.button('Scrape'):
        job_postings_df = scrape_job_postings(n_pages)

        if not job_postings_df.empty:
            st.write("Total number of job postings scraped:", len(job_postings_df))
            st.write("Average Salary:", job_postings_df['job_salary'].mean())

            # Formatting salary values for pie chart labels
            job_postings_df['formatted_salary'] = job_postings_df['job_salary'].apply(format_salary_value)

            # Visualization - Salary Distribution (Pie Chart)
            st.subheader("Salary Distribution")
            salary_counts = job_postings_df['formatted_salary'].value_counts().dropna()
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(salary_counts, labels=salary_counts.index, autopct='%1.1f%%', startangle=140)
            ax.axis('equal')
            st.pyplot(fig)

            # Top 5 Highest Paying Jobs
            st.subheader("Top 5 Highest Paying Jobs")
            highest_paying_jobs = job_postings_df.nlargest(5, 'job_salary')
            st.table(highest_paying_jobs[['job_title', 'job_salary']])

            # Top 5 Lowest Paying Jobs
            st.subheader("Top 5 Lowest Paying Jobs")
            lowest_paying_jobs = job_postings_df.nsmallest(5, 'job_salary')
            st.table(lowest_paying_jobs[['job_title', 'job_salary']])

            # Job with Longest Title
            st.subheader("Job with the Longest Title")
            longest_title_job = job_postings_df.loc[job_postings_df['job_title'].str.len().idxmax()]
            st.write(longest_title_job['job_title'])

if __name__ == "__main__":
    main()