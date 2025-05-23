import uuid
import time
import random
from typing import List, Dict, Tuple
from .utils import error_log, success_log, info_log, debug_log

class TournamentManager:
    def __init__(self, api, config):
        self.api = api
        self.config = config
        self.tournament_types = {
            "bronze": {"max_stars": 18, "name": "Bronze Tournament"},
            "silver": {"max_stars": 23, "name": "Silver Tournament"},
            "gold": {"max_stars": 25, "name": "Gold Tournament"},
            "elite": {"max_stars": float('inf'), "name": "Elite Tournament"}
        }
        
    def fetch_player_cards(self, wallet_address: str, token: str, account_number: int) -> List[Dict]:
        try:
            privy_id_token = None
            for cookie in self.api.session.cookies:
                if cookie.name == 'privy-id-token':
                    privy_id_token = cookie.value
                    break
            
            auth_token = privy_id_token if privy_id_token else token
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Authorization': f'Bearer {auth_token}',
                'Origin': 'https://monad.fantasy.top',
                'Referer': 'https://monad.fantasy.top/',
                'User-Agent': self.api.user_agent,
                'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=1, i'
            }
            
            page = 1
            limit = 100
            cards = []
            
            while True:
                params = {
                    'pagination.page': page,
                    'pagination.limit': limit,
                    'where.rarity.in': [1, 2, 3, 4],
                    'orderBy': 'cards_score_desc',
                    'groupCard': 'true',
                    'isGalleryView': 'false'
                }
                
                response = self.api.session.get(
                    f'https://secret-api.fantasy.top/card/player/{wallet_address}',
                    headers=headers,
                    params=params,
                    proxies=self.api.proxies,
                    timeout=15
                )
                
                if response.status_code == 429:
                    info_log(f"Rate limit hit while fetching cards for account {account_number} {response.text}, retrying...")
                    continue
                
                if response.status_code == 401:
                    if auth_token == privy_id_token and token:
                        auth_token = token
                        headers['Authorization'] = f'Bearer {auth_token}'
                        continue
                    
                    error_log(f"Authorization failed while fetching cards for account {account_number}")
                    return []
                
                if response.status_code != 200:
                    error_log(f"Failed to fetch cards for account {account_number}: {response.status_code}")
                    debug_log(f"Response: {response.text[:200]}")
                    return []
                
                data = response.json()
                if not data.get('data'):
                    break
                    
                for card in data.get('data', []):
                    if not card.get('is_in_deck', False):
                        processed_card = {
                            'id': card.get('id'),
                            'heroes': {
                                'name': card.get('name', card.get('heroes', {}).get('name', 'Unknown')),
                                'handle': card.get('handle', card.get('heroes', {}).get('handle', 'Unknown')),
                                'stars': card.get('stars', card.get('heroes', {}).get('stars', 0))
                            },
                            'card_weighted_score': card.get('card_weighted_score', card.get('weighted_score', 0))
                        }
                        cards.append(processed_card)
                
                meta = data.get('meta', {})
                current_page = meta.get('currentPage', 0)
                last_page = meta.get('lastPage', 0)
                
                if current_page >= last_page or not meta:
                    break
                    
                page += 1
            
            success_log(f"Fetched {len(cards)} available cards for account {account_number}")
            return cards
            
        except Exception as e:
            error_log(f"Error fetching cards for account {account_number}: {str(e)}")
            return []
    

    def select_best_cards_for_tournament(self, cards: List[Dict], max_stars: int, used_card_ids: List[str]) -> Tuple[List[Dict], int]:
        try:
            available_cards = [card for card in cards if card['id'] not in used_card_ids]
            
            if len(available_cards) < 5:
                return [], 0
                
            def get_stars_safe(card):
                try:
                    return int(card.get('heroes', {}).get('stars', 0))
                except (ValueError, TypeError):
                    return 0
                    
            sorted_cards = sorted(available_cards, key=get_stars_safe, reverse=True)
            
            best_selection = self._find_optimal_card_selection(sorted_cards, max_stars)
            
            if not best_selection or len(best_selection) < 5:
                sorted_by_stars_asc = sorted(available_cards, key=get_stars_safe)
                best_selection = sorted_by_stars_asc[:5]
            
            total_stars = 0
            for card in best_selection:
                try:
                    total_stars += int(card.get('heroes', {}).get('stars', 0))
                except (ValueError, TypeError):
                    pass
                
            return best_selection, total_stars
            
        except Exception as e:
            error_log(f"Error in select_best_cards_for_tournament: {str(e)}")
            return [], 0
    
    def _find_optimal_card_selection(self, sorted_cards: List[Dict], max_stars: int) -> List[Dict]:
        if len(sorted_cards) < 5:
            return []
            
        selected = []
        total_stars = 0
        
        for card in sorted_cards:
            try:
                card_stars = int(card.get('heroes', {}).get('stars', 0))
            except (ValueError, TypeError):
                card_stars = 0
                
            if card_stars + total_stars <= max_stars:
                selected.append(card)
                total_stars += card_stars
                if len(selected) == 5:
                    break
        
        if len(selected) == 5:
            return selected

        selected = []
        total_stars = 0
        
        value_sorted = []
        for card in sorted_cards:
            try:
                stars = int(card.get('heroes', {}).get('stars', 1))
                if stars <= 0:
                    stars = 1
                    
                weighted_score = float(card.get('card_weighted_score', 0))
                ratio = weighted_score / stars
                
                value_sorted.append((card, ratio))
            except (ValueError, TypeError):
                value_sorted.append((card, 0))
        
        value_sorted.sort(key=lambda x: x[1], reverse=True)
        
        sorted_by_value = [item[0] for item in value_sorted]
        
        for card in sorted_by_value:
            try:
                card_stars = int(card.get('heroes', {}).get('stars', 0))
            except (ValueError, TypeError):
                card_stars = 0
                
            if card_stars + total_stars <= max_stars:
                selected.append(card)
                total_stars += card_stars
                if len(selected) == 5:
                    break
        
        if len(selected) == 5:
            return selected
            
        try:
            sorted_by_stars = sorted(sorted_cards, 
                                    key=lambda x: int(x.get('heroes', {}).get('stars', 0)))
            return sorted_by_stars[:5]
        except (ValueError, TypeError):
            return sorted_cards[:5]
    
    def register_for_tournament(self, token: str, wallet_address: str, account_number: int, 
                               tournament_id: str, card_ids: List[str], deck_number: int = 1) -> bool:
        try:
            privy_id_token = None
            for cookie in self.api.session.cookies:
                if cookie.name == 'privy-id-token':
                    privy_id_token = cookie.value
                    break
            
            auth_token = privy_id_token if privy_id_token else token
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json',
                'Origin': 'https://monad.fantasy.top',
                'Referer': 'https://monad.fantasy.top/',
                'User-Agent': self.api.user_agent,
                'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'Priority': 'u=1, i'
            }
            
            max_registration_retries = 5
            retry_delay = 2
            timeout_duration = 15
            
            for retry_attempt in range(max_registration_retries):
                try:
                    deck_id = str(uuid.uuid4())
                    
                    payload = {
                        "deckId": deck_id,
                        "cardIds": card_ids,
                        "tournamentId": tournament_id
                    }
                    
                    debug_log(f"Sending tournament registration payload: {payload}")
                    
                    response = self.api.session.post(
                        'https://secret-api.fantasy.top/tournaments/create-deck',
                        headers=headers,
                        json=payload,
                        proxies=self.api.proxies,
                        timeout=15
                    )
                    
                    try:
                        response_data = response.json()
                        debug_log(f"Tournament registration response: {response_data}")
                    except Exception:
                        debug_log(f"Non-JSON response: {response.text}")
                    
                    if response.status_code == 400:
                        info_log(f"Response ... {response.text}")
                        time.sleep(retry_delay)
                        continue

                    if response.status_code == 429:
                        info_log(f"Rate limit hit during tournament registration for account {account_number}, retrying ({retry_attempt+1}/{max_registration_retries})...")
                        time.sleep(retry_delay)
                        continue
                    
                    if response.status_code == 500:
                        info_log(f"Server error (500) during tournament registration for account {account_number}, retrying ({retry_attempt+1}/{max_registration_retries})...")
                        time.sleep(retry_delay)
                        time.sleep(random.uniform(1.0, 3.0))
                        continue
                    
                    if response.status_code == 401 and auth_token == privy_id_token and token:
                        auth_token = token
                        headers['Authorization'] = f'Bearer {auth_token}'
                        continue
                    
                    if response.status_code in [200, 201]:
                        success_log(f"Successfully registered account {account_number} in tournament {tournament_id} (Deck #{deck_number})")
                        return True
                        
                    info_log(f"Unknown response {response.status_code} during tournament registration for account {account_number}, retrying ({retry_attempt+1}/{max_registration_retries})...")
                    debug_log(f"Registration response: {response.text}")
                    time.sleep(retry_delay)
                    
                except Exception as e:
                    if retry_attempt < max_registration_retries - 1:
                        error_log(f"Error during tournament registration attempt {retry_attempt+1}: {str(e)}, retrying...")
                        time.sleep(retry_delay)
                    else:
                        error_log(f"Error during tournament registration attempt {retry_attempt+1}: {str(e)}")
            
            # After 3 retries, rotate proxy and wait before trying again
            info_log(f"Failed to register for tournament after {max_registration_retries} attempts. Rotating proxy and waiting {timeout_duration} seconds...")
            
            # Rotate proxy if available
            if hasattr(self.api, 'rotate_proxy') and callable(getattr(self.api, 'rotate_proxy')):
                self.api.rotate_proxy()
                info_log(f"Proxy rotated for account {account_number}")
            else:
                info_log(f"Proxy rotation not available for account {account_number}")
            
            # Wait for the specified timeout
            time.sleep(timeout_duration)
                
                # Continue the outer loop to try again
                
        except Exception as e:
            error_log(f"Error registering for tournament: {str(e)}")
            return False
    
    def register_in_tournaments(self, token: str, wallet_address: str, account_number: int, 
                                   tournament_ids: Dict[str, str]) -> Dict[str, bool]:
        results = {}
        cards = self.fetch_player_cards(wallet_address, token, account_number)
        
        if not cards:
            info_log(f"No cards available for account {account_number}")
            return {t_type: False for t_type in tournament_ids.keys()}
        
        active_tournament_type = None
        for t_type, t_id in tournament_ids.items():
            if t_id:
                active_tournament_type = t_type
                break
        
        if not active_tournament_type:
            info_log(f"No active tournament selected for account {account_number}")
            return {}
        
        tournament_id = tournament_ids[active_tournament_type]
        max_stars = self.tournament_types[active_tournament_type]["max_stars"]
        
        info_log(f"Attempting to register account {account_number} in {active_tournament_type.capitalize()} tournament")
        
        used_card_ids = []
        deck_number = 1
        registration_successful = False
        
        while True:
            selected_cards, total_stars = self.select_best_cards_for_tournament(cards, max_stars, used_card_ids)
            
            if len(selected_cards) < 5:
                if deck_number == 1:
                    info_log(f"Not enough available cards for {active_tournament_type} tournament for account {account_number}")
                    results[active_tournament_type] = False
                else:
                    info_log(f"No more complete decks available for {active_tournament_type} tournament (registered {deck_number-1} decks)")
                break
                
            if total_stars > max_stars:
                if deck_number == 1:
                    info_log(f"Selected cards exceed star limit for {active_tournament_type} tournament: {total_stars} > {max_stars}")
                    results[active_tournament_type] = False
                else:
                    info_log(f"No more valid decks within star limit for {active_tournament_type} tournament")
                break
                
            card_ids = [card['id'] for card in selected_cards]
            
            try:
                clean_card_info = []
                for card in selected_cards:
                    name = card.get('heroes', {}).get('name', 'Unknown')
                    clean_name = ''.join(c for c in name if ord(c) < 128)
                    stars = card.get('heroes', {}).get('stars', 0)
                    clean_card_info.append(f"{clean_name} ({stars}*)")
                
                info_log(f"Selected cards for {active_tournament_type} tournament deck #{deck_number} (total {total_stars}*): {', '.join(clean_card_info)}")
                
                success = self.register_for_tournament(token, wallet_address, account_number, tournament_id, card_ids, deck_number)
                
                if success:
                    used_card_ids.extend(card_ids)
                    registration_successful = True
                    deck_number += 1
                else:
                    if deck_number == 1:
                        results[active_tournament_type] = False
                    break
            except Exception as e:
                error_log(f"Error registering for {active_tournament_type} tournament: {str(e)}")
                if deck_number == 1:
                    results[active_tournament_type] = False
                break
        
        results[active_tournament_type] = registration_successful
        return results
