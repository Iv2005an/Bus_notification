from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)
driver.get('https://ciox.ru/check-user-agent')
soup = BeautifulSoup(driver.page_source, 'lxml')
driver.quit()
u_a = str(soup.find('br').next)
print(u_a.lstrip().rstrip())
