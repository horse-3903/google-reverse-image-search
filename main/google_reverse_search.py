from playwright.sync_api import Page, Playwright, Browser, BrowserContext, sync_playwright, TimeoutError as PlaywrightTimeout
from os.path import isfile
import validators

def _startup_() -> list:
    """
    Startup process to open browser and contexts
    
    Ensures that Closing process is smooth
    
    Goes to https://www.google.com.my/imghp in preparation for querying

    Returns
    ---------
    `[playwright.sync_api.Page, playwright.sync_api.Browser, playwright.sync_api.BrowserContext]`
    """
    p:Playwright = sync_playwright().start()
    browser = p.chromium.launch() # change to False for debugging
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.google.com.my/imghp") # goes to image search
    print("Connected...")
    return [page, browser, context]

def search_with_url(url:str, num:int = 5) -> None:
    """
    Searches using URL on the web
    
    Will raise `validators.utils.ValidationFailure` upon invalidity
    
    Calls the function `results_to_json`

    Returns
    ---------
    `None`
    """
    page:Page
    browser:Browser
    context:BrowserContext
    page, browser, context = _startup_()
    valid = validators.url(url)
    if valid:
        page.get_by_role("button", name="Search by image").click()
        url_input = page.get_by_placeholder("Paste image link")
        url_input.hover()
        url_input.type(url)
        page.get_by_role("button",name="Search",exact=True).first.click()
        page.goto(page.get_by_role("link", name="Find image source").get_attribute("href"))

        results = results_to_json(page=page, lens=True, num=num)
        browser.close()
        context.close()
        return results
    else:
        browser.close()
        context.close()
        raise valid

def search_with_file(file_path:str, num:int = 5) -> None:
    """
    Searches using file on the web
    
    Will raise `FileNotFoundError` upon invalidity
    
    Calls the function `results_to_json`

    Returns
    ---------
    `None`
    """
    page:Page
    browser:Browser
    context:BrowserContext
    page, browser, context = _startup_()

    if not isfile(file_path):
        browser.close()
        context.close()
        raise FileNotFoundError
    page.get_by_role("button", name="Search by image").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_text("upload a file").click()
    file_chooser = fc_info.value
    file_chooser.set_files(file_path)
    page.goto(page.get_by_role("link", name="Find image source").get_attribute("href"))
    
    results = results_to_json(page=page, lens=True, num=num)
    browser.close()
    context.close()
    return results

def search_with_query(query:str, num:int = 5):
    """
    Searches using a query on the web
    
    Calls the function `results_to_json`

    Returns
    ---------
    `None`
    """
    page:Page
    browser:Browser
    context:BrowserContext
    page, browser, context = _startup_()

    query_input = page.get_by_role("combobox",name="Search")
    query_input.hover()
    query_input.type(query)
    query_input.press("Enter")
    
    results = results_to_json(page=page, lens=False, num=num)
    browser.close()
    context.close()
    return results

def results_to_json(page:Page, lens:bool, num:int = 5) -> dict:
    """
    Referred from `search_with_query()`, `search_with_url()` and `search_with_file()`
    
    Takes lens in case of the last 2 functions above, redirecting to the image carousel

    Returns
    ---------
    ```
    {
        "title" : str,
        "data" : [
            "link" : str,
            "name" : str,
            "dimensions" : [int, int]
        ]
    }
    ```
    """
    if lens:
        nav_url:str = page.url
        print("Navigating...")
        while True:
            try:
                page.wait_for_selector("'Tools'").hover()
                page.wait_for_selector("'Tools'").click()
                break
            except:
                pass

        page.get_by_role("button", name="Search by image").filter(has_text="Search by image").click()
        page.get_by_role("menuitemradio").filter(has_text="More sizes").click()
        try:
            if page.wait_for_selector("text='Looks like there aren’t any matches for your search'",timeout=1000).is_visible():
                page.go_back()
                while True:
                    try:
                        page.wait_for_selector("'Tools'").hover()
                        page.wait_for_selector("'Tools'").click()
                        break
                    except:
                        pass
                if {"y":True,"n":False}[(input("Do you wish to continue with less accurate results? [Y]/n : ").lower() or "y")]:
                    page.get_by_role("button", name="Search by image").filter(has_text="Search by image").click()
                    page.get_by_role("menuitemradio").filter(has_text="Visually similar").click()
                else:
                    return {}

        except PlaywrightTimeout:
            pass

    while True:
        try:
            page.wait_for_selector("'Tools'").hover()
            page.wait_for_selector("'Tools'").click()
            break
        except:
            pass
    page.get_by_role("button",name="Size").first.click()
    size:list = ["Large","Medium","Any size"]
    size_idx = 0
    page.get_by_role("link", name=size[size_idx]).filter(has_text=size[size_idx]).click()
    loc = page.get_by_text("Image results").locator("../div")
    suc = 0
    idx = 0
    links:list = []
    size_idx += 1

    print("Getting results...")
    while suc < num:
        if (idx >= int(loc.last.get_attribute("data-ri"))+1):
            if size_idx > 2:
                print(f"WARNING : Could only find {len(links)} photos")
                if {"y":True,"n":False}[(input("Do you wish to continue with less accurate results? [Y]/n : ").lower() or "y")]:
                    page.goto(nav_url)
                    while True:
                        try:
                            page.wait_for_selector("'Tools'").hover()
                            page.wait_for_selector("'Tools'").click()
                            break
                        except:
                            pass
                    page.get_by_role("button", name="Search by image").filter(has_text="Search by image").click()
                    page.get_by_role("menuitemradio").filter(has_text="Visually similar").click()
                    loc = page.get_by_text("Image results").locator("../div")
                    size_idx += 1
                    idx = 0

                else: 
                    return {
                        "title":page.locator("input[role='combobox'][aria-label='Search']").get_attribute("value"),
                        "data":links
                    }
            else:
                page.get_by_role("listitem").first.click()
                page.get_by_role("link", name=size[size_idx]).filter(has_text=size[size_idx]).click()
                loc = page.get_by_text("Image results").locator("../div")
                size_idx += 1
                idx = 0
        div = loc.nth(idx)
        div.click()

        cur_img = page.locator("img[class='n3VNCb KAlRDb']")
        try:
            cur_img.inner_html(timeout=1000)
        except PlaywrightTimeout:
            idx += 1
            continue
        
        if cur_img.get_attribute("src").find("data") != 0:
            links.append({
                "link":cur_img.get_attribute("src"),
                "name":cur_img.get_attribute("alt"),
                "dimensions":[int(i.replace(",","")) for i in cur_img.locator("//../span").text_content().split(" × ")]
            })
            idx += 1
            suc += 1
        else:
            idx += 1
    
    print("Preparing results...")
    return {
        "title":page.locator("input[role='combobox'][aria-label='Search']").get_attribute("value"),
        "data":links
    }
    