import time
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
webdriver_path = r'C:\Users\ralha\OneDrive\Desktop\IIITB\chromedriver.exe'



def get_profile_urls(pub_url):
    
    ''' 
        :Params:
         pub_url - URL link of a medium publication i.e. https://medium.com/search/users?q=towards%20data%20science

        :Description:
         Scrapes links related to user profiles from a publication page. i.e. https://medium.com/@kozyrkov
         
        :Returns:
         Returns a list of user names and user profile urls
         
    '''

    # Store search results
    user_names = []
    user_urls = []

    # Path to webdriver
    browser = webdriver.Chrome(webdriver_path)

    # URL to scrape
    browser.get(pub_url)
    time.sleep(1)

    # Get body
    elem = browser.find_element_by_tag_name("body")

    # No. of times to scroll
    no_of_pagedowns = 100

    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)
        no_of_pagedowns-=1

    # Get tag
    a_tag = browser.find_elements_by_class_name("link.link--primary.u-accentColor--hoverTextNormal")

    for a in a_tag:
        user_names.append(a.text)
        user_urls.append(a.get_attribute("href"))

    browser.quit()

    print(f'No. of usernames: {len(user_names)}')
    print(user_names[-5:])
    print(f'No. of urls: {len(user_urls)}')
    print(user_urls[-5:])
    
    return user_names, user_urls



def get_writer_profile(browser,writer_profile_df,writer_profiles_col):
    
    ''' 
        :Params:
         browser - Selenium's browser session
         writer_profile_df - A pandas dataframe where new post entries are appended to
         writer_profiles_col - List of columns names in "writer_profile_df"

        :Description:
         "get_writer_profile" extracts information from each post, creates a new entry for "writer_profile_df" and appends it.
         Any posts that fails to be extracted is ignored and an error counter is kept.
         
        :Returns:
         Returns "writer_profile_df" with new appended entries and an error count
         
    '''
    
    # Initialize List
    user_name, user_profile_desc, user_followers, top_writer_flag = [],[],[],[]
        
    # Get user_name 
    match_tag = browser.find_element_by_tag_name("h1")
    user_name.append(match_tag.text)

    # Get user_profile_desc
    match_tag = browser.find_element_by_tag_name("p")
    user_profile_desc.append(match_tag.text)

    # Get user_followers
    try:
        match_tag = browser.find_element_by_partial_link_text("Followers")
        if match_tag.text.split()[0][-1]=="K":
            user_followers.append(float(match_tag.text.split()[0][:-1]) * 1000)
        else:
            user_followers.append(float(match_tag.text.split()[0]))
    except:
        user_followers.append(float(0))
        pass

    # Get top_writer_flag
    try:
        match_tag = browser.find_elements_by_tag_name("span")
        count=1
        for match in match_tag:
            if "Top writer" in match.text:
                top_writer_flag.append(float(1))
                break
            else:
                if count==5:
                    top_writer_flag.append(float(0))
                    break
                count+=1
    except:
        pass
    
    writer_profile ={
                     'user_name': user_name,
                     'user_profile_desc': user_profile_desc,
                     'user_followers': user_followers,
                     'top_writer_flag':top_writer_flag
                    }
    
    df_mismatch = 0
    try:
        # Create new entry
        create_new_entry = pd.DataFrame(writer_profile, columns = writer_profiles_col)

        # Appends new entry to posts_df
        writer_profile_df = writer_profile_df.append(create_new_entry, ignore_index=True)
    except:
        df_mismatch+=1
        pass
    
    return writer_profile_df, df_mismatch



def get_posts(browser,posts_df,post_details_col):
        
    ''' 
        :Params:
         browser - Selenium's browser session
         posts_df - A pandas dataframe where new post entries are appended to
         post_details_col - List of columns names in "posts_df"

        :Description:
         "get_posts" extracts information from each post, creates a new entry for "posts_df" and appends it.
         Any posts that fails to be extracted is ignored and an error counter is kept.
         
        :Returns:
         Returns "posts_df" with new appended entries and an error count
         
    '''
    
    # Switch to beautifulsoup for bulk of extraction
    page_content = BeautifulSoup(browser.page_source,"html.parser")

    # Loops through each post
    df_mismatch = 0
    ends_with_yc = re.compile(r'(..\s){5}y c')
    for row in page_content.find_all('div', class_=ends_with_yc):

        # Reset list
        user_name, title, publisher, claps, date_posted, read_time= [],[],[],[],[],[]

        # Search for title
        try:
            title_tag = row.find_all('h1')[0]
            title.append(title_tag.text)
        except:
            title.append("")
            pass

        # Search for user_name and publisher_name
        try:
            pub_tag = row.find_all('span')[0].find('div')
            publisher.append(' '.join(pub_tag.text.split()[pub_tag.text.split().index("in")+1:]))
            user_name.append(' '.join(pub_tag.text.split()[:pub_tag.text.split().index("in")]))
        except:
            publisher.append(pub_tag)
            user_name.append(pub_tag)
            pass

        # Search for claps
        try:
            claps_tag = row.find_all('h4')[0].text
            if claps_tag[-1]=="K":
                claps.append(float(claps_tag[:-1]) * 1000)
            else:
                claps.append(float(claps_tag))
        except:
            # Post with no claps do not have H4 tag
            claps.append(float(0))
            pass

        # Search for date_posted and read_time
        try:
            dp_rt_tag = row.find_all('span')[3].find('div')
            dp_tag = dp_rt_tag.text.split('·')[0]
            rt_tag = float(dp_rt_tag.text.split('·')[1].split()[0])
            date_posted.append(dp_tag.strip())
            read_time.append(rt_tag)
        except:
            pass

        # Post details
        post_details = {
                        'user_name': user_name,
                        'title': title,
                        'publisher': publisher,
                        'claps': claps,
                        'date_posted': date_posted,
                        'read_time':read_time
                        }

        try:
            # Create new entry
            create_new_entry = pd.DataFrame(post_details, columns = post_details_col)

            # Appends new entry to posts_df
            posts_df = posts_df.append(create_new_entry, ignore_index=True)
        except:
            df_mismatch+=1
            pass
    
    return posts_df, df_mismatch



def extract_information(url,posts_df,writer_profile_df,post_details_col,writer_profiles_col):
    
    ''' 
        :Params:
         url - A user's profile link i.e. https://medium.com/@kozyrkov
         posts_df - A pandas dataframe where new post entries are appended to
         writer_profile_df - A pandas dataframe where new profile entries are appended to
         post_details_col - List of column names in "posts_df"
         writer_profiles_col - List of column names in "writer_profile_df"

        :Description:
         Initilizes a Selenium browser for each URL recieved to being extraction process
         
        :Returns:
         Returns "posts_df" and "writer_profile_df" with new appended entries and a consolidated error count
         
    '''
    
    # Path to webdriver
    browser = webdriver.Chrome(webdriver_path)
    
    # URL to scrape
    browser.get(url)
    time.sleep(1)

    # Get body
    elem = browser.find_element_by_tag_name("body")

    # No. of times to scroll
    no_of_pagedowns = 100

    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)
        no_of_pagedowns-=1
        
    # Get posts
    posts_df, error_count_post = get_posts(browser,posts_df,post_details_col)

    # Get profiles
    writer_profile_df, error_count_profiles = get_writer_profile(browser,writer_profile_df,writer_profiles_col)
    
    error_count = error_count_post + error_count_profiles;
    
    browser.quit()
    
    return posts_df, writer_profile_df, error_count


# url_list = ['https://medium.com/@kozyrkov','https://medium.com/@ssrosa','https://medium.com/@neha_mangal','https://medium.com/@parulnith']

# Get profile urls
_,url_list = get_profile_urls("https://medium.com/search/users?q=towards%20data%20science")

# Set column names
writer_profiles_col = ["user_name", "user_profile_desc", "user_followers", "top_writer_flag"]
post_details_col = ["user_name", "title", "publisher", "claps", "date_posted", "read_time"]

# Initalize empty dfs
writer_profile_df = pd.DataFrame(None, columns = writer_profiles_col)
posts_df = pd.DataFrame(None, columns = post_details_col)

# Loop through URL list
t0 = datetime.now()
time_counter = 0
error_count = 0
save_state = 0
for url in url_list:
    
    time_counter += 1
    sys.stdout.write("Processed: %s / %s \r" % (time_counter, len(url_list)))
    sys.stdout.flush()
    
    posts_df, writer_profile_df, error_retrieved = extract_information(url,posts_df,writer_profile_df,post_details_col,writer_profiles_col)
    
    error_count += error_retrieved
    
    # save to csv every 50 urls
    if save_state%50==1:
        # Write to CSVs
        writer_profile_df.to_csv(r'C:\Users\tds_scrape\writer_profile_df.csv')
        posts_df.to_csv(r'C:\Users\tds_scrape\posts_df.csv')
    
    save_state+=1
    
    print("Processed: %s / %s -- Elapse Time: %s" % (time_counter,len(url_list),datetime.now()-t0))
    print(f"Errors due to input mismatch: {error_count}")
    
# Write to CSVs
writer_profile_df.to_csv(r'C:\Users\writer_profile_df.csv')
posts_df.to_csv(r'C:\Users\posts_df.csv')


print(writer_profile_df)

print("\n")

print(posts_df)



