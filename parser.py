from selenium import webdriver
from bs4 import BeautifulSoup


def time_to_bus(stop_link, name_bus):
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(options=op)
    driver.get(stop_link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    name_stop = soup.find('h1', class_='card-title-view__title').text
    buses = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    for bus in buses:
        if bus.text == name_bus:
            t_to_bus = bus.find_next(class_='masstransit-prognoses-view__title-text').text
            return name_stop, t_to_bus


print(time_to_bus('https://yandex.ru/maps/213/moscow/stops/stop__9642091/?ll=37.604492%2C55.633689&tab=overview&z=18.01',
                  'н8 (ночной)'))
