import telebot
from telebot import types
from django.core.management.base import BaseCommand
from django.conf import  settings
from core.models import Client



class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = telebot.TeleBot(settings.TOKEN, parse_mode=None)

        @bot.message_handler(commands=['start'])
        def ask_user_name(message):
            bot.send_message(message.chat.id, 'Здравствуйте, как вас зовут?')
            bot.register_next_step_handler(message, get_user_name)

        def get_user_name(message):
            Client.objects.update_or_create(
                user_id=message.from_user.id,
                defaults={
                    'name': message.text,
                }
            )
            markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=10)
            send_button = types.KeyboardButton('Отправить номер телефона', request_contact=True)
            markup.add(send_button)

            bot.send_message(message.chat.id, 'Пришлите, пожалуйста, Ваш номер телефона.', reply_markup=markup)
            bot.register_next_step_handler(message, get_phone)

        def get_phone(message):
            if message.contact:
                try:
                    client = Client.objects.get(user_id=message.from_user.id)
                    client.phone = message.contact.phone_number
                    client.save()
                except AttributeError:
                    bot.send_message(message.chat.id, 'Не удалось получить номер телефона. Попробуйте ещё раз.')
                    bot.register_next_step_handler(message, get_phone)
                else:
                    markup = types.ReplyKeyboardRemove()
                    bot.send_message(message.chat.id, 'Пришлите фотографию с штрихкодом.', reply_markup=markup)
                    bot.register_next_step_handler(message, get_code)
            else:
                bot.send_message(message.chat.id, 'Нажмите на кнопку ниже.')
                bot.register_next_step_handler(message, get_phone)

        @bot.message_handler(content_types=['photo'])
        def get_code(message):
            print(message.photo)
            markup = types.InlineKeyboardMarkup(row_width=2)
            score_button = types.InlineKeyboardButton('Мои баллы', callback_data='score')
            codes_button = types.InlineKeyboardButton('Мои коды', callback_data='codes')
            markup.add(score_button, codes_button)
            if message.photo:
                bot.send_message(message.chat.id, 'Штрихкод обработан.', reply_markup=markup)

        # else:
        # 	bot.send_message(message.chat.id, 'Штрихкод обработан.')

        # def get_user_phone(message):
        # 	print(message.text)
        # 	bot.send_message(message.chat.id, f'Ваш номер телефона: {message.text}')
        # 	# bot.register_next_step_handler(message, ask_user_phone)

        bot.polling()
