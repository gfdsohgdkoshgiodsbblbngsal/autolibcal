import asyncio
import aiohttp
from bs4 import BeautifulSoup

from typing import Union, Dict

async def get_study_rooms(date: str) -> Union[tuple, str]:
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
                return 'Reached end of booking window.'
            if soup.select_one('.s-lc-period-closed'):
                # print(soup.select_one('.s-lc-period-closed'))
                return 'No study rooms available.'

            slots = soup.find_all(attrs={'class': 's-lc-eq-period-content'})
            # print(slots)
            available_slots = []
            formatted_slots = [] # [({0, 1, 2, 3}, 2024-09-05 09:30:00, 2024-09-05 10:30:00)]
            # Each period is an element
            # each element is a tuple consisting of a list that has what study rooms are available, start and end times of the period
            for i in range(0, 24, 4):
                # print(i)
                slot = slots[i].select_one('.s-lc-eq-period')
                formatted_slots.append((set(), slot['data-period-start'], slot['data-period-end']))
            for i, s in enumerate(slots):
                available = s.select_one('.s-lc-eq-period-available')
                if available:
                    available_slots.append(i)
            
            # print(available_slots)
            
            for a in available_slots:
                formatted_slots[a%6][0].add(a//6)
    
    # print(formatted_slots)
    return (formatted_slots, [e.string for e in soup.find_all(attrs={'class': 's-lc-period-name'})])

if __name__ == "__main__":
    asyncio.run(get_study_rooms("2024-09-13"))