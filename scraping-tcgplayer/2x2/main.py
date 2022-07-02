import json
from datetime import date
from scraper import scrape_tcgplayer_2x2 as scrape

cs = 91
us = 80
rs = 120
ms = 40
b_cs = 9
b_us = 21
b_rs = 30
b_ms = 20
t_ms = 5

styles = ['Normal', 'Foil', 'Etched Foil', 'Borderless', 'Borderless Foil', 'Textured Foil']
price_cutoff = 1.99


def scryfall_db():
    local_scryfall = "D:/Documents/Games/Magic/scryfall-dbs/all-cards-latest.json"
    with open(local_scryfall, 'r', encoding='utf8') as db:
        allcards = json.load(db)
    double_masters = [card for card in allcards if card['set'] == '2x2']
    return double_masters


def tcgplayer_nonfoils():
    local_tcgplayer = 'tcgplayer_2x2_nonfoils.json'
    with open(local_tcgplayer, 'r', encoding='utf8') as f:
        return json.load(f)


def tcgplayer_foils():
    local_tcgplayer = 'tcgplayer_2x2_foils.json'
    with open(local_tcgplayer, 'r', encoding='utf8') as f:
        return json.load(f)


def parce_price(card, style):
    if 'marketPrice' in card:
        foil = 'Foil' in style
        foil_only = card['foilOnly'] == 'true'
        if foil == foil_only:
            return float(card['marketPrice'])

    prices = []
    for listing in card['listings']:
        finish = listing['printing']
        if listing['condition'] == 'Near Mint' and \
                'Foil' in style and finish == 'Foil' \
                or 'Foil' not in style and finish == 'Normal':
            prices.append(float(listing['price']))

    return 0.0 if len(prices) == 0 else min(prices)


def parse_card_data(nonfoils, foils):
    cards = {}
    for card in nonfoils:
        product_name = card['productName']

        if 'Token' in product_name or 'Emblem' in product_name:
            continue

        name = product_name
        style = 'Normal'

        if "Borderless" in product_name:
            name = product_name[:-len(' (Borderless)')]
            style = 'Borderless'
        elif "Etched" in product_name:
            name = product_name[:-len(' (Foil Etched)')]
            style = 'Etched Foil'
        elif "Textured" in product_name:
            name = product_name[:-len(' (Textured Foil)')]
            style = 'Textured Foil'
        elif "Etcherd" in product_name:
            name = 'Master Biomancer'
            style = 'Etched Foil'

        if name not in cards:
            cards[name] = {}
            cards[name]['Rarity'] = 'L'\
                if name == 'Cryptic Spires'\
                else card['customAttributes']['rarityDbName']
        elif style in cards[name]:
            print(f'duplicate style {style} for {name}')
            continue

        cards[name][style] = parce_price(card, style)
        cn = int(card['customAttributes']['number'])
        if cn < 333:
            cards[name]['CN'] = cn

    for card in foils:
        product_name = card['productName']

        if 'Token' in product_name \
                or 'Emblem' in product_name \
                or 'Etched' in product_name \
                or 'Etcherd' in product_name \
                or 'Textured' in product_name:
            continue

        name = product_name
        style = 'Foil'

        if "Borderless" in product_name:
            name = product_name[:-len(' (Borderless)')]
            style = 'Borderless Foil'

        if name not in cards:
            cards[name] = {}
        elif style in cards[name]:
            print(f'duplicate style {style} for {name}')
            continue

        cards[name][style] = parce_price(card, style)

    return cards


def log(cards):
    for name, prices in cards.items():
        print(name)
        for style in styles:
            print(f'{style}: {"-" if style not in prices else prices[style]}')
        print()


def write_card_prices(cards, today=True):
    with open(f"prices-{date.today() if today else 'previous'}.txt", 'w', encoding='utf8') as out:
        out.write('CN')
        out.write('\tName')
        out.write('\tRarity')
        for style in styles:
            out.write(f'\t{style}')
        out.write('\n')

        for name, prices in cards.items():
            out.write(f'{"" if "CN" not in prices else prices["CN"]}')
            out.write('\t'+name)
            out.write('\t'+prices['Rarity'])
            for style in styles:
                out.write(f'\t{"-" if style not in prices else prices[style]}')
            out.write('\n')


def rarity_ev(cards, rarity, style):
    n = 0
    if rarity == 'C':
        n = b_cs if 'Borderless' in style else cs
    elif rarity == 'U':
        n = b_us if 'Borderless' in style else us
    elif rarity == 'R':
        n = b_rs if 'Borderless' in style else rs
    else:
        n = t_ms if 'Textured' in style else b_ms if 'Borderless' in style else ms

    cards_of_rarity = {card: values for card, values in cards.items()
                       if values['Rarity'] == rarity
                       and style in values
                       and values[style] >= price_cutoff}
    ev = sum([card[style] for card in cards_of_rarity.values()]) / n
    return ev


def calc_evs(cards):
    # common slot
    common_borderless_rate = b_cs/cs/3
    common_ev = (1 - common_borderless_rate) * rarity_ev(cards, 'C', 'Normal')
    common_borderless_ev = common_borderless_rate * rarity_ev(cards, 'C', 'Borderless')
    common_slot_ev = common_ev + common_borderless_ev

    # uncommon slot
    uncommon_borderless_rate = b_us/us/3
    uncommon_slot_ev = ((1 - uncommon_borderless_rate) * rarity_ev(cards, 'U', 'Normal')) + \
                       (uncommon_borderless_rate * rarity_ev(cards, 'U', 'Borderless'))

    # rare/mythic slot
    rm_ev = 7/8 * rarity_ev(cards, 'R', 'Normal') + 1/8 * rarity_ev(cards, 'M', 'Normal')
    borderless_rm_ev = 7/8 * rarity_ev(cards, 'R', 'Borderless') + 1/8 * rarity_ev(cards, 'M', 'Borderless')

    rm_slot_ev = 8/9 * rm_ev + 1/9 * borderless_rm_ev

    # draft foil slot
    draft_common_foil_rate = 10/14
    draft_uncommon_foil_rate = 3/14
    draft_rm_foil_rate = 1/14

    common_foil_ev = ((1 - common_borderless_rate) * rarity_ev(cards, 'C', 'Foil')) +\
                           (common_borderless_rate * rarity_ev(cards, 'C', 'Borderless Foil'))

    uncommon_foil_ev = ((1 - uncommon_borderless_rate) * rarity_ev(cards, 'U', 'Foil')) + \
                             (uncommon_borderless_rate * rarity_ev(cards, 'U', 'Borderless Foil'))

    rm_foil_ev = 7/8 * rarity_ev(cards, 'R', 'Foil') + 1/8 * rarity_ev(cards, 'M', 'Foil')

    draft_rm_borderless_foil_ev = 7/8 * rarity_ev(cards, 'R', 'Borderless Foil') + \
                                  1/8 * rarity_ev(cards, 'M', 'Borderless Foil')

    draft_foil_slot_ev = (1-0.0125) * (draft_common_foil_rate * common_foil_ev +
                                       draft_uncommon_foil_rate * uncommon_foil_ev +
                                       draft_rm_foil_rate * rm_foil_ev) + 0.0125 * draft_rm_borderless_foil_ev

    draft_booster = 2 * rm_slot_ev + 2 * draft_foil_slot_ev + 3 * uncommon_slot_ev + 8 * common_slot_ev + \
                    cards['Cryptic Spires']['Normal']

    # collector foil slot
    collector_common_rate = 10/13
    collector_uncommon_rate = 3/13

    collector_cu_borderless_slot = collector_common_rate * rarity_ev(cards, 'C', 'Borderless') + \
        collector_uncommon_rate * rarity_ev(cards, 'U', 'Borderless')

    collector_cu_borderless_foil_slot = collector_common_rate * rarity_ev(cards, 'C', 'Borderless Foil') + \
        collector_uncommon_rate * rarity_ev(cards, 'U', 'Borderless Foil')

    collector_rm_borderless_ev = 7/8 * rarity_ev(cards, 'R', 'Borderless') + \
                                 1/8 * rarity_ev(cards, 'M', 'Borderless')

    etched_ev = 7/8 * rarity_ev(cards, 'R', 'Etched Foil') + 1/8 * rarity_ev(cards, 'M', 'Etched Foil')

    collector_rm_borderless_foil_ev = 7/8 * rarity_ev(cards, 'R', 'Borderless Foil') + \
                                      1/8 * rarity_ev(cards, 'M', 'Borderless Foil')

    collector_rm_borderless_foil_slot = .97 * collector_rm_borderless_foil_ev + \
                                        0.03 * rarity_ev(cards, 'M', 'Textured Foil')

    collector_booster = 5 * common_foil_ev + 2 * uncommon_foil_ev + 2 * collector_cu_borderless_slot + \
                        2 * collector_cu_borderless_foil_slot + rm_foil_ev + collector_rm_borderless_ev + etched_ev + \
                        collector_rm_borderless_foil_slot

    return draft_booster, collector_booster


def parse_prev():
    cards = {}
    with open('prices-previous.txt', 'r', encoding='utf-8') as f:
        # for line in map(str.split, f.readlines()):
        for line in map(lambda s: s.strip().split('\t'), f.readlines()[1:]):
            name = line[1]
            cards[name] = {}
            cards[name]['Rarity'] = line[2]

            for idx, style in enumerate(styles):
                price = line[idx+3]
                cards[name][style] = float(price) if price.replace('.', '').isdigit() else 0.0

    return cards


def print_evs(evs):
    print('\t\t\tbooster\tbox')
    print(f'draft:\t\t{evs[0]:.2f}\t{evs[0]*24:.2f}')
    print(f'collector:\t{evs[1]:.2f}\t{evs[1]*4:.2f}')


def calc_Δs(cards, prev_cards):
    Δs = {}
    for card, prices in cards.items():
        prev_prices = prev_cards[card]
        Δs[card] = {style: ((prices[style] if style in prices else 0.0)
                            - (prev_prices[style] if style in prev_prices else 0.0))
                    for style in styles}

    max_Δs = [(card, max(map(abs, prices.values()))) for card, prices in Δs.items()]
    max_Δs.sort(key=lambda cΔ: -cΔ[1])

    # for i in range(10):
    #     card_name, Δ = max_Δs[i]
    #     print(card_name)
    #     for style, price in Δs[card_name].items():
    #         print(f'{style}: {price:.2f}')
    #     print()

    for card_name, Δ in max_Δs[:10]:
        print(card_name)
        for style, price in Δs[card_name].items():
            print(f'{style}: {price:.2f}')
        print()


def main():
    # scrape()
    print('reading card data...')
    nonfoils = tcgplayer_nonfoils()
    foils = tcgplayer_foils()
    cards = parse_card_data(nonfoils, foils)
    print('done reading card data.')
    print('writing to file...')
    write_card_prices(cards)
    print('done writing to file')
    #log(cards)
    print()
    print(f'Prices for {date.today()}:')
    evs = calc_evs(cards)
    print_evs(evs)
    print()
    print(f'Prices for yesterday:')
    prev_cards = parse_prev()
    prev_evs = calc_evs(prev_cards)
    print_evs(prev_evs)
    print()
    calc_Δs(cards, prev_cards)

    # write_card_prices(cards, today=False)


if __name__ == "__main__":
    main()
