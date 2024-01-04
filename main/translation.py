from googletrans import Translator

translator = Translator()


def translate_text(text, dest_language):
    translation = translator.translate(text, dest=dest_language)
    return translation.text
