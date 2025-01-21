from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
from selenium.webdriver.common.action_chains import ActionChains

def setup_chrome_with_profile():
    # Kill any existing Chrome processes
    os.system("taskkill /f /im chrome.exe")
    time.sleep(2)  # Wait for processes to close
    
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=C:\\Users\\xlkay\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_argument("profile-directory=Default")
    # Add these options to help prevent crashes
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error starting Chrome: {str(e)}")
        print("Please ensure Chrome is fully closed and try again.")
        exit(1)

def make_posts_private(driver, channel_url):
    # Ensure URL starts with https://
    if not channel_url.startswith('https://'):
        channel_url = 'https://' + channel_url.replace('x.com', 'twitter.com')
    elif 'x.com' in channel_url:
        channel_url = channel_url.replace('x.com', 'twitter.com')
    
    print(f"Navigating to: {channel_url}")
    # Navigate to the specified channel
    driver.get(channel_url)
    
    # Wait for timeline to load
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
        )
    except TimeoutException:
        print("Timeline failed to load")
        return
    
    time.sleep(5)  # Additional wait for dynamic content
    
    # Updated JavaScript function to find and click the More button
    find_and_click_js = """
    function findAndClickMore() {
        // Find all tweets
        const tweets = document.querySelectorAll('[data-testid="tweet"]');
        if (tweets.length === 0) return false;
        
        // Get the first tweet
        const tweet = tweets[0];
        
        // Find the More button within this tweet using the exact structure from the screenshot
        const moreButton = tweet.querySelector('div[aria-label="More"][role="button"][data-testid="caret"]');
        if (!moreButton) {
            console.log("More button not found, trying alternative selector...");
            // Try alternative selector
            const altMoreButton = tweet.querySelector('[data-testid="caret"]');
            if (!altMoreButton) return false;
            
            // Create and dispatch click event
            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: altMoreButton.getBoundingClientRect().x + 5,
                clientY: altMoreButton.getBoundingClientRect().y + 5
            });
            altMoreButton.dispatchEvent(clickEvent);
            return true;
        }
        
        // Create and dispatch click event
        const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: moreButton.getBoundingClientRect().x + 5,
            clientY: moreButton.getBoundingClientRect().y + 5
        });
        moreButton.dispatchEvent(clickEvent);
        return true;
    }
    return findAndClickMore();
    """
    
    # Updated JavaScript function to click menu options
    click_menu_option_js = """
    function clickMenuOption(text) {
        // Wait a bit for the menu to be fully visible
        const menuItems = Array.from(document.querySelectorAll('div[role="menuitem"] span'));
        const menuItem = menuItems.find(item => item.textContent.includes(text));
        if (menuItem) {
            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: menuItem.getBoundingClientRect().x + 5,
                clientY: menuItem.getBoundingClientRect().y + 5
            });
            menuItem.dispatchEvent(clickEvent);
            return true;
        }
        return false;
    }
    return clickMenuOption(arguments[0]);
    """
    
    # Track processed posts by their unique IDs
    processed_post_ids = set()
    total_found_posts = 0
    no_scroll_count = 0
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    
    # Try to get total posts from profile
    try:
        time.sleep(5)  # Wait for page to load
        total_posts_element = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="primaryColumn"] div[dir="ltr"] span')
        expected_total = int(total_posts_element.text.split()[0])
        print(f"\nExpected total posts: {expected_total}")
    except Exception as e:
        print("Could not determine expected total posts count")
        expected_total = None
    
    while True:
        try:
            # Wait for posts to be visible
            posts = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
            )
            
            if not posts:
                print("No more posts found")
                break
            
            # Get unique IDs for current posts
            current_post_ids = set()
            for post in posts:
                try:
                    post_id = post.get_attribute("data-testid") + "_" + post.get_attribute("aria-labelledby")
                    current_post_ids.add(post_id)
                except:
                    continue
            
            # Calculate new posts found
            new_posts = len(current_post_ids - processed_post_ids)
            total_found_posts += new_posts
            
            print(f"\nFound {new_posts} new posts (Total found: {total_found_posts})")
            if expected_total:
                print(f"Progress: {total_found_posts}/{expected_total} ({(total_found_posts/expected_total*100):.1f}%)")
            
            # Update processed posts set
            processed_post_ids.update(current_post_ids)
            
            # Try to click More button using JavaScript
            more_clicked = driver.execute_script(find_and_click_js)
            
            if more_clicked:
                print("Successfully processed a post")
                # Click "Change who can reply"
                if driver.execute_script(click_menu_option_js, "Change who can reply"):
                    print("Clicked 'Change who can reply'")
                    time.sleep(2)
                    
                    # Click "Only you"
                    if driver.execute_script(click_menu_option_js, "Only you"):
                        print("Successfully made post private")
                        time.sleep(2)
                    else:
                        print("Could not find 'Only you' option")
                else:
                    print("Could not find 'Change who can reply' option")
            else:
                print("Could not find More button")
            
            # Scroll and check if we've reached the end
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                no_scroll_count += 1
                if no_scroll_count >= 3:  # Try 3 times before concluding we're at the end
                    print("\nReached the end of the timeline")
                    if expected_total and total_found_posts < expected_total:
                        print(f"Note: Only found {total_found_posts} out of {expected_total} expected posts")
                    break
            else:
                no_scroll_count = 0
                last_height = new_height
            
        except Exception as e:
            print(f"Error processing post: {str(e)}")
            continue

    print(f"\nCompleted! Processed {total_found_posts} posts in total.")

def main():
    channel_url = input("Please enter the Twitter channel URL: ").strip()
    driver = setup_chrome_with_profile()
    
    try:
        make_posts_private(driver, channel_url)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
