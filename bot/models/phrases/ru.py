from pydantic import BaseModel, Field
from typing import Dict, List

from ...enums import Gender, HeightParams
from ..config_model import ConfigModel

class Ru(BaseModel):

    bot_started: str = Field("Bot {me.username} started!")

    register_message_text: str = Field("")
    register_button_text: str = Field("")
    genders_map: Dict[str, Gender] = Field(
        {
            "Мужской": Gender.male,
            "Женский": Gender.female,
        }
    )
    select_gender_message_text: str = Field("Выбери свой пол")
    enter_name_message_text: str = Field("Введи свое имя")
    enter_age_message_text: str = Field("Введи свой возраст (число лет)")
    enter_height_message_text: str = Field("Введи свой рост в сантиметрах")
    enter_weight_message_text: str = Field("Введи свой вес в килограмах")
    select_city_message_text: str = Field("Выбери свой город")
    enter_about_text_message_text: str = Field("")
    skip_button_text: str = Field("Пропустить")
    enter_voice_message_text: str = Field("")
    use_current_button_text: str = Field("")
    select_relationships_type_message_text: str = Field("")
    enter_photos_message_text: str = Field("")
    save_button_text: str = Field("")
    edit_button_text: str = Field("")
    work_sheet_no_about_fmt: str = Field(
        "{sheet.name}, {sheet.age}, {sheet.city}\n{sheet.height} см"
    )
    work_sheet_about_fmt: str = Field("")
    work_sheet_intst_and_about_fmt: str = Field("")
    work_sheet_no_intst_and_about_fmt: str = Field("")
    confirm_text: str = Field("")

    work_sheet_reply_markup_message_text: str = Field("⬇️")
    work_sheet_created_message_text: str = Field("Твоя анкета успешно создана")
    edit_params_button_text: str = Field("Редактировать анкету")
    start_search_button_text: str = Field("Начать поиск")
    stop_search_button_text: str = Field("Прекратить поиск")
    remove_work_sheet_button_text: str = Field("Удалить анкету")
    send_location_button_text: str = Field("")

    edit_work_sheet_button_text: str = Field("")
    edit_work_sheet_photo_button_text: str = Field("")
    edit_work_sheet_about_button_text: str  = Field("")
    edit_work_sheet_instagram_button_text: str = Field("")
    start_search_button_text_2: str = Field("")

    edit_search_params_button_text: str = Field("Изменить параметры поиска")
    main_menu_button_text: str = Field("Меню")
    edit_params_message_text: str = Field("Выбери, что ты хочешь отредактировать")
    params_changed_message_text: str = Field("Параметры поиска отредактированы")
    use_menu_buttons_message_text: str = Field("Используй кнопки в меню ниже")
    like_button_text: str = Field("💖")
    dislike_button_text: str = Field("👎")
    no_search_result_message_text: str = Field(
        "Ты просмотрел(а) все анкеты. Подходящие анкеты не найдены"
    )
    like_message_text: str = Field("Кому-то понравилась твоя анкета")
    answer_button_text: str = Field("Ответить")
    work_sheet_reveal_message_text_fmt: str = Field(
        "Вы понравились друг другу. Не теряйте время. Начните общаться - {bot_user.username}"
    )
    search_stopped_message_text: str = Field("Твоя анкета отключена")
    should_enter_photo: str = Field("Необходимо загрузить одно или несколько фото")
    my_work_sheet_button_text: str = Field("Моя анкета")
    like_count_message_text_fmt: str = Field(
        "Ты понравился {count} людям. Показать анкеты?"
    )
    yes_button_text: str = Field("Да")
    no_button_text: str = Field("Нет")
    inlvaid_command: str = Field("⚠️ Неизвестная команда")
    subscription_text: str = Field(
        "Для продолжения работы бота необходимо подписаться на наш канал {link}"
    )
    your_work_sheet_text: str = Field("")
    my_work_sheet_menu_text: str = Field("")
    enter_instagram_text_message_text: str = Field("")


    @property
    def genders(self):
        return tuple(self.genders_map.keys())

    @property
    def reversed_genders_map(self):
        return {v: k for k, v in self.genders_map.items()}

class En(BaseModel):

    bot_started: str = Field("Bot {me.username} success started!")
    register_message_text: str = Field("")
    register_button_text: str = Field("")
    genders_map: Dict[str, Gender] = Field(
        {
            "Мужской": Gender.male,
            "Женский": Gender.female,
        }
    )
    select_gender_message_text: str = Field("Выбери свой пол")
    enter_name_message_text: str = Field("Введи свое имя")
    enter_age_message_text: str = Field("Введи свой возраст (число лет)")
    enter_height_message_text: str = Field("Введи свой рост в сантиметрах")
    enter_weight_message_text: str = Field("Введи свой вес в килограмах")
    select_city_message_text: str = Field("Выбери свой город")
    enter_about_text_message_text: str = Field("")
    skip_button_text: str = Field("Пропустить")
    enter_voice_message_text: str = Field("")
    use_current_button_text: str = Field("")
    select_relationships_type_message_text: str = Field("")
    enter_photos_message_text: str = Field("")
    save_button_text: str = Field("")
    edit_button_text: str = Field("")
    work_sheet_no_about_fmt: str = Field(
        "{sheet.name}, {sheet.age}, {sheet.city}\n{sheet.height} см"
    )
    work_sheet_about_fmt: str = Field(
        "{sheet.name}, {sheet.age}, {sheet.city}\n{sheet.height} см\n\nО себе: {sheet.about_text}"
    )
    work_sheet_intst_and_about_fmt: str = Field("")
    work_sheet_no_intst_and_about_fmt: str = Field("")
    confirm_text: str = Field("")
    
    work_sheet_reply_markup_message_text: str = Field("⬇️")
    work_sheet_created_message_text: str = Field("Твоя анкета успешно создана")
    edit_params_button_text: str = Field("Редактировать анкету")
    start_search_button_text: str = Field("Начать поиск")
    stop_search_button_text: str = Field("Прекратить поиск")
    remove_work_sheet_button_text: str = Field("Удалить анкету")
    send_location_button_text: str = Field("")

    edit_work_sheet_button_text: str = Field("")
    edit_work_sheet_photo_button_text: str = Field("")
    edit_work_sheet_about_button_text: str  = Field("")
    edit_work_sheet_instagram_button_text: str = Field("")
    start_search_button_text_2: str = Field("")

    edit_search_params_button_text: str = Field("Изменить параметры поиска")
    main_menu_button_text: str = Field("Меню")
    edit_params_message_text: str = Field("Выбери, что ты хочешь отредактировать")
    params_changed_message_text: str = Field("Параметры поиска отредактированы")
    use_menu_buttons_message_text: str = Field("Используй кнопки в меню ниже")
    like_button_text: str = Field("💖")
    dislike_button_text: str = Field("👎")
    no_search_result_message_text: str = Field(
        "Ты просмотрел(а) все анкеты. Подходящие анкеты не найдены"
    )
    like_message_text: str = Field("Кому-то понравилась твоя анкета")
    answer_button_text: str = Field("Ответить")
    work_sheet_reveal_message_text_fmt: str = Field(
        "Вы понравились друг другу. Не теряйте время. Начните общаться - {bot_user.username}"
    )
    search_stopped_message_text: str = Field("Твоя анкета отключена")
    should_enter_photo: str = Field("Необходимо загрузить одно или несколько фото")
    my_work_sheet_button_text: str = Field("Моя анкета")
    like_count_message_text_fmt: str = Field(
        "Ты понравился {count} людям. Показать анкеты?"
    )
    yes_button_text: str = Field("Да")
    no_button_text: str = Field("Нет")
    inlvaid_command: str = Field("⚠️ Неизвестная команда")
    subscription_text: str = Field(
        "Для продолжения работы бота необходимо подписаться на наш канал {link}"
    )
    your_work_sheet_text: str = Field("")
    my_work_sheet_menu_text: str = Field("")
    enter_instagram_text_message_text: str = Field("")

    @property
    def genders(self):
        return tuple(self.genders_map.keys())

    @property
    def reversed_genders_map(self):
        return {v: k for k, v in self.genders_map.items()}