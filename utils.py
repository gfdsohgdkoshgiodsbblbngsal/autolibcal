import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def get_study_rooms(date: str):
    url = "https://mitty.libcal.com/ajax/equipment/k12/availability"
    
    headers = {
        "accept": "text/html, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://mitty.libcal.com",
        "referer": "https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    data = {
        "lid": "20936",
        "gid": "44085",
        "zone": "0",
        "eid": "0",
        "seatId": "0",
        "date": date,
        "capacity": "1",
        "pageIndex": "0",
        "pageSize": "10"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            res = await response.text()
            soup = BeautifulSoup(res, 'lxml')

            if soup.select_one('#s-lc-window-limit-warning'):
                print('Reached end of booking window')
                return
            if soup.select_one('.s-lc-period-closed'):
                print('No Slots Avaliable')
                return

            slots = soup.find_all(attrs={'class': 's-lc-eq-period-content'})
            for i, s in enumerate(slots):
                avaliable = s.select_one('.s-lc-eq-period-available')
                if avaliable:
                    print(i+1)
                    print(' '.join(avaliable['data-period-display'].strip().split()))

        # async with session.get('https://mitty.libcal.com/r/new/availability?lid=20936&zone=0&gid=44085&capacity=1') as response:
        #     res = await response.text()
        #     soup = BeautifulSoup(res, 'html.parser')

        #     print(soup.find_all(attrs={'class': 's-lc-eq-period-content'}))