from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
#from RPA.Assistant import Assistant

@task
def order_robots_from_robotSpareBin():
    """ Orders robots from RobotspareBin Industries Inc.
        Saves the order HTML receipt as a pdf file.
        Saves the screen shot of the ordered robot
        Embeds the screenshot of the robot to the PDF receipt
        Create Zip file archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    download_csv_file()
    read_orders_csv()

"""def user_input_task():
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text_input("text_input", placeholder="Please enter URL")
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input"""

def open_robot_order_website():
    browser.goto('https://robotsparebinindustries.com/#/robot-order')
 
def download_csv_file():
    """download the csv orders data from provided URL"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def read_orders_csv():
    """Read the orders.csv and place result in orders table"""
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number","Head","Body","Legs","Address"], delimiters=",", header=True
    )
    """ Process the orders table"""
    for row in orders:
        clear_model()
        fill_order_form(row)
        handle_place_order()
        is_order_error = False
        error_check = check_for_submit_error(is_order_error)
        while  error_check == True:
               handle_place_order()
               error_check = check_for_submit_error(is_order_error) 

        screenshot_path = screenshot_robot(row['Order number'])

        create_pdf_of_order_receipt(row['Order number'], screenshot_path)
        process_another_order()
    zip_receipts()

def fill_order_form(order):
    """ Fill the order form with csv file rows"""
    page = browser.page()
    page.locator('#head').select_option(order['Head'])
    page.locator(f'#id-body-{order["Body"]}').click()
    page.get_by_placeholder('Enter the part number for the legs').fill(order['Legs'])
    page.locator('#address').fill(order['Address'])

    """ Preview the robot image"""
    page.locator('#preview').click()

def handle_place_order():
    """ Submit the order """

    page = browser.page()
    page.locator('#order').click()

def process_another_order():
    """ Process the next order row from csv file"""

    page = browser.page()
    page.locator('#order-another').click()

def check_for_submit_error(is_order_error):
    """ Check for error when submitting the order"""
    page = browser.page()
    try:
        page.wait_for_selector(selector='.alert-danger', timeout=2000)
        is_order_error = True
       
    except PlaywrightTimeoutError:
            is_order_error = False
            None
    return(is_order_error)

def clear_model():
    """ Clear the popup model"""

    page = browser.page()
    page.locator('button', has_text='OK').click()

def screenshot_robot(order_number):
    """ take Screen shot of the robot image"""

    screenshot_path = f'./output/created-robot/{order_number}-robot.png'
    page = browser.page()
    page.locator('#robot-preview-image').screenshot(path=screenshot_path)
    receipt_html = page.locator('#receipt').inner_html()
    
    return screenshot_path

def create_pdf_of_order_receipt(order_number, screenshot_path):
    """ create PDF of order"""

    receipt_path = f'./output/receipts/{order_number}-receipt.pdf'

    page = browser.page()
    receipt_html = page.locator('#receipt').inner_html()
    
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, receipt_path)
    
    pdf.add_files_to_pdf(files=[screenshot_path], target_document=receipt_path, append=True)

def zip_receipts():
    """ Zip the receipts"""

    archive = Archive()
    archive.archive_folder_with_zip(folder='./output/receipts', archive_name='./output/receipts/receipts.zip')   