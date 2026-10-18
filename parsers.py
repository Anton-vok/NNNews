def parse_title(text):
    if len(text) > 80:
        raise ValueError("Слишком длинное, до 80 символов")
    return text.strip()

def parse_url(text):
    return text
def parse_date(text):
    return text