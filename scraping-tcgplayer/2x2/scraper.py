import requests
import pandas as pd
import json


def scrape_tcgplayer_2x2():
    url = "https://mpapi.tcgplayer.com/v2/search/request"

    querystring = {"q":"","isList":"true"}

    payload = {
        "algorithm": "",
        "from": 0,
        "size": 610,
        "filters": {
            "term": {
                "productLineName": ["magic"],
                "setName": ["double-masters-2022"],
                "productTypeName": ["Cards"]
            },
            "range": {},
            "match": {}
        },
        "listingSearch": {
            "filters": {
                "term": {
                    "sellerStatus": "Live",
                    "channelId": 0
                },
                "range": {"quantity": {"gte": 1}},
                "exclude": {"channelExclusion": 0}
            },
            "context": {"cart": {}}
        },
        "context": {
            "cart": {},
            "shippingCountry": "US"
        },
        "sort": {
            "field": "product-name",
            "order": "asc"
        }
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Origin": "https://www.tcgplayer.com",
        "Connection": "keep-alive",
        "Referer": "https://www.tcgplayer.com/",
        # "Cookie": "tcg-uuid=caac5ba4-0c99-467e-9cfd-4891889d8b50; valid=set=true; amp_b98ea9_tcgplayer.com=xy59Qpko-d808N504cYtMr.MDE0ZDBmY2EtMjI0MC00YzBjLTlmMGItNmEzZTJiYjc1MmE0..1fvkfdu72.1fvkfdu74.37p.2q.3aj; product-display-settings=sort=price+shipping&size=10; setting=CD=US&M=1; AWSALB=39r2IHWxW66VFaSRvANJT65D9eHuNxrYOHEjPcL4uSl7bkACNsz0TpXCA/Xh5HT7dKQMBXhPj3OZoFVHGpe1YLNqKGt31KtDpUUsVffydRj+MrX8eRy1IpKVfZMw; AWSALBCORS=39r2IHWxW66VFaSRvANJT65D9eHuNxrYOHEjPcL4uSl7bkACNsz0TpXCA/Xh5HT7dKQMBXhPj3OZoFVHGpe1YLNqKGt31KtDpUUsVffydRj+MrX8eRy1IpKVfZMw; TCG_Data=M=1&SearchGameNameID=magic; TCG_VisitorKey=9eceb1ec-6ed4-4cdf-8838-edf8c28b2178; TCG_VisitorKey=6c70e8c8-0c36-416f-89e9-4ab23a688d25; SearchSortSettings=M=1&ProductSortOption=ProductName&ProductSortDesc=False&PriceSortOption=Shipping&ProductResultDisplay=list",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "DNT": "1",
        "Sec-GPC": "1",
        "TE": "trailers"
    }

    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
    data = response.json()
    cards = data['results'][0]['results']

    with open('tcgplayer_2x2_nonfoils.json', 'w', encoding='utf8') as json_out:
        json.dump(cards, json_out)

    payload['filters']['term']['printing'] = ["Foil"]

    response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
    data = response.json()
    cards = data['results'][0]['results']
    with open('tcgplayer_2x2_foils.json', 'w', encoding='utf8') as json_out:
        json.dump(cards, json_out)


if __name__ == '__main__':
    print('getting price data from tcg player...')
    scrape_tcgplayer_2x2()
    print('done scraping.')
