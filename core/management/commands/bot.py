import requests
import telebot
import os.path
from telebot import types
import zbar
from matplotlib.image import imread as read_image
import zbar.misc
from django.core.management.base import BaseCommand
from django.conf import  settings
from core.models import Client, Code


scanner = zbar.Scanner()


def imread(image_filename):
    image = read_image(image_filename)
    if len(image.shape) == 3:
        image = zbar.misc.rgb2gray(image)
    return image


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
            if message.photo:
                file_id = message.photo[0].file_id
                file_info = bot.get_file(file_id)
                photo = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(settings.TOKEN, file_info.file_path))

                with open(os.path.join(settings.BASE_DIR, file_info.file_path), 'wb') as f:
                    f.write(photo.content)
                
                image_as_numpy_array = imread(file_info.file_path)
                results = scanner.scan(image_as_numpy_array)
                if not results:
                    bot.send_message(message.chat.id, 'Штрихкод не распознан.')
                
                client = Client.objects.get(user_id=message.from_user.id)
                for result in results:
                    code = Code.objects.filter(code=result.data.decode('utf8'))
                    if not code:
                        bot.send_message(message.chat.id, 'Штрихкод не найден.')
                    code = code.filter(client=None).first()
                    if code:
                        code.client = client
                        code.save()

                        client.score += code.points
                        client.save()
                    else:
                        bot.send_message(message.chat.id, 'Штрихкод уже вводился.')

                markup = types.InlineKeyboardMarkup(row_width=2)
                score_button = types.InlineKeyboardButton('Мои баллы', callback_data='score')
                codes_button = types.InlineKeyboardButton('Мои коды', callback_data='codes')
                markup.add(score_button, codes_button)
                bot.send_message(message.chat.id, 'Штрихкод обработан.', reply_markup=markup)

        @bot.callback_query_handler(lambda query: query.data == 'score')
        def get_user_score(query):
            client = Client.objects.get(user_id=query.from_user.id)
            bot.send_message(query.message.chat.id, f'Ваши баллы: {client.score}')

        @bot.callback_query_handler(lambda query: query.data == 'codes')
        def get_user_score(query):
            codes = Code.objects.filter(client__user_id=query.from_user.id)
            text = '\n'.join(f'{i}. {code.code}' for i, code in enumerate(1, codes))
            bot.send_message(query.message.chat.id, text)

        bot.polling()
