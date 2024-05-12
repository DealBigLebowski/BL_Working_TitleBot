from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    pass

class SearchState(StatesGroup):
    waiting_action = State()

class Action(StatesGroup):
    wait_action = State()
    wait_start_advertising_text = State()
    wait_advertising_text = State()
    wait_chat_data = State()
    wait_notify_chat_data = State()
    wait_user_people = State()
    wait_other_send_request = State()
    wait_support_username = State()
    wait_company_name = State()
    wait_clover_limit_amount = State()
    wait_clover_bounty_data = State()
    wait_set_rates = State()
    wait_scrap_set_rates = State()
    wait_add_rek_fio = State()
    wait_add_rek_bank = State()
    wait_add_rek_limit = State()
    wait_add_rek_other_information = State()
    wait_game_username = State()
    wait_user_profite_commission = State()
    wait_select_rek_amount = State()
    wait_sletter_text = State()