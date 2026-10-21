set -e

echo "Создаю виртуальное окружение..."
python3 -m venv .venv

echo "Активирую виртуальное окружение и устанавливаю зависимости..."
. .venv/bin/activate
pip install -r requirements.txt

echo "Настройка успешно завершена!"