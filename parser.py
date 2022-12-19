from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

op = webdriver.ChromeOptions()
op.add_argument('headless')
ChromeDriverManager(path="drivers").install()
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=op)


def name_stop(stop_link, name_bus):
    driver.get(stop_link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    name_stop = soup.find('h1', class_='card-title-view__title').text
    buses = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    for bus in buses:
        if bus.text == name_bus:
            t_to_bus = bus.find_next(class_='masstransit-prognoses-view__title-text').text
            return name_stop, t_to_bus


print(name_stop('https://yandex.ru/maps/213/moscow/stops/stop__9642284/?ll=37.621979%2C55.786906&tab=overview&z=17.53',
                'м53'))
