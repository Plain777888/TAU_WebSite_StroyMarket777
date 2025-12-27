import os
import django
from decimal import Decimal

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'construction_store.settings')
django.setup()

from store.models import Category, Product, ProductImage


def create_categories():
    """Создание категорий товаров"""
    categories_data = [
        {
            'name': 'Инструменты',
            'slug': 'tools',
            'description': 'Ручные и электрические инструменты для строительства и ремонта'
        },
        {
            'name': 'Крепеж',
            'slug': 'fasteners',
            'description': 'Болты, гайки, шурупы, дюбели и другой крепежный материал'
        },
        {
            'name': 'Электроинструмент',
            'slug': 'power-tools',
            'description': 'Электрические инструменты для профессионального и домашнего использования'
        },
        {
            'name': 'Электрика',
            'slug': 'electrical',
            'description': 'Провода, розетки, выключатели, автоматы и другая электрофурнитура'
        },
        {
            'name': 'Сантехника',
            'slug': 'plumbing',
            'description': 'Трубы, фитинги, смесители, раковины и другое сантехническое оборудование'
        },
        {
            'name': 'Отделочные материалы',
            'slug': 'finishing',
            'description': 'Шпаклевка, краска, обои, плитка и другие отделочные материалы'
        },
        {
            'name': 'Лакокрасочные материалы',
            'slug': 'paint',
            'description': 'Краски, лаки, эмали, грунтовки и растворители'
        },
        {
            'name': 'Строительные смеси',
            'slug': 'building-mixes',
            'description': 'Цемент, штукатурка, шпаклевка, клеевые смеси'
        },
        {
            'name': 'Измерительные инструменты',
            'slug': 'measuring-tools',
            'description': 'Рулетки, уровни, угольники, лазерные нивелиры'
        },
        {
            'name': 'Средства защиты',
            'slug': 'protection',
            'description': 'Перчатки, очки, респираторы, каски и другая защитная экипировка'
        },
    ]

    for cat_data in categories_data:
        Category.objects.get_or_create(
            name=cat_data['name'],
            slug=cat_data['slug'],
            defaults={'description': cat_data['description']}
        )

    print(f"Создано {len(categories_data)} категорий")
    return Category.objects.all()


def create_products():
    """Создание товаров"""

    # Получаем категории
    tools = Category.objects.get(slug='tools')
    fasteners = Category.objects.get(slug='fasteners')
    power_tools = Category.objects.get(slug='power-tools')
    electrical = Category.objects.get(slug='electrical')
    plumbing = Category.objects.get(slug='plumbing')
    finishing = Category.objects.get(slug='finishing')
    paint = Category.objects.get(slug='paint')
    building_mixes = Category.objects.get(slug='building-mixes')
    measuring = Category.objects.get(slug='measuring-tools')
    protection = Category.objects.get(slug='protection')

    products_data = [
        # ИНСТРУМЕНТЫ
        {
            'category': tools,
            'name': 'Молоток слесарный 500г',
            'slug': 'hammer-500g',
            'price': Decimal('899.99'),
            'unit': 'шт',
            'stock': 45,
            'brand': 'ЗУБР',
            'description': 'Молоток слесарный с деревянной рукояткой. Вес бойка: 500г. Идеально подходит для домашнего использования.',
            'material': 'Сталь, дерево',
            'weight': Decimal('0.7'),
            'color': 'Стальной'
        },
        {
            'category': tools,
            'name': 'Набор отверток 6 предметов',
            'slug': 'screwdriver-set-6',
            'price': Decimal('1299.50'),
            'unit': 'набор',
            'stock': 32,
            'brand': 'STAYER',
            'description': 'Набор отверток с различными насадками: плоские и крестовые. Рукоятки с противоскользящим покрытием.',
            'material': 'Сталь, пластик',
            'weight': Decimal('0.45'),
            'color': 'Разноцветный'
        },
        {
            'category': tools,
            'name': 'Плоскогубцы 180мм',
            'slug': 'pliers-180mm',
            'price': Decimal('649.99'),
            'unit': 'шт',
            'stock': 28,
            'brand': 'ЗУБР',
            'description': 'Плоскогубцы комбинированные с изолированными рукоятками. Длина: 180мм.',
            'material': 'Хромованадиевая сталь',
            'weight': Decimal('0.32'),
            'color': 'Хромированный'
        },

        # КРЕПЕЖ
        {
            'category': fasteners,
            'name': 'Саморезы по дереву 4.2x70мм',
            'slug': 'wood-screws-4-2x70',
            'price': Decimal('249.99'),
            'unit': 'уп',
            'stock': 120,
            'brand': 'KREP',
            'description': 'Саморезы по дереву, оцинкованные. Упаковка 200шт. Идеальны для деревянных конструкций.',
            'material': 'Оцинкованная сталь',
            'weight': Decimal('0.85'),
            'dimensions': '4.2x70мм'
        },
        {
            'category': fasteners,
            'name': 'Дюбель-гвоздь 6x40мм',
            'slug': 'dowel-nail-6x40',
            'price': Decimal('189.99'),
            'unit': 'уп',
            'stock': 95,
            'brand': 'KREP',
            'description': 'Дюбель-гвоздь для быстрого монтажа. Упаковка 100шт. Подходит для бетона и кирпича.',
            'material': 'Пластик, сталь',
            'weight': Decimal('0.35'),
            'dimensions': '6x40мм'
        },
        {
            'category': fasteners,
            'name': 'Анкерный болт М10х100',
            'slug': 'anchor-bolt-m10x100',
            'price': Decimal('89.99'),
            'unit': 'шт',
            'stock': 150,
            'brand': 'FISCHER',
            'description': 'Анкерный болт для надежного крепления в бетоне. Высокая несущая способность.',
            'material': 'Оцинкованная сталь',
            'weight': Decimal('0.12'),
            'dimensions': 'М10х100мм'
        },

        # ЭЛЕКТРОИНСТРУМЕНТ
        {
            'category': power_tools,
            'name': 'Дрель-шуруповерт 18В',
            'slug': 'drill-driver-18v',
            'price': Decimal('5499.99'),
            'unit': 'шт',
            'stock': 15,
            'brand': 'BOSCH',
            'description': 'Беспроводной дрель-шуруповерт с двумя аккумуляторами. Крутящий момент: 50Нм.',
            'material': 'Пластик, металл',
            'weight': Decimal('1.4'),
            'color': 'Синий'
        },
        {
            'category': power_tools,
            'name': 'Перфоратор 800Вт',
            'slug': 'perforator-800w',
            'price': Decimal('7999.99'),
            'unit': 'шт',
            'stock': 8,
            'brand': 'MAKITA',
            'description': 'Перфоратор с режимами сверления и удара. Мощность: 800Вт. Регулировка скорости.',
            'material': 'Пластик, металл',
            'weight': Decimal('2.8'),
            'color': 'Бирюзовый'
        },
        {
            'category': power_tools,
            'name': 'Циркулярная пила 1200Вт',
            'slug': 'circular-saw-1200w',
            'price': Decimal('4599.99'),
            'unit': 'шт',
            'stock': 12,
            'brand': 'ЭНЕРГОМАШ',
            'description': 'Циркулярная пила с диском 185мм. Глубина пропила: 65мм. Защитный кожух.',
            'material': 'Пластик, металл',
            'weight': Decimal('4.2'),
            'color': 'Оранжевый'
        },

        # ЭЛЕКТРИКА
        {
            'category': electrical,
            'name': 'Розетка двойная с заземлением',
            'slug': 'socket-double-grounded',
            'price': Decimal('349.99'),
            'unit': 'шт',
            'stock': 65,
            'brand': 'LEGRAND',
            'description': 'Розетка двойная скрытого монтажа с заземлением. Цвет: белый.',
            'material': 'Пластик, латунь',
            'color': 'Белый'
        },
        {
            'category': electrical,
            'name': 'Выключатель одноклавишный',
            'slug': 'switch-single',
            'price': Decimal('279.99'),
            'unit': 'шт',
            'stock': 78,
            'brand': 'SCHNEIDER',
            'description': 'Выключатель скрытого монтажа для освещения. Одноклавишный.',
            'material': 'Пластик',
            'color': 'Белый'
        },
        {
            'category': electrical,
            'name': 'Кабель ВВГнг 3x2.5',
            'slug': 'cable-vvgng-3x2-5',
            'price': Decimal('89.99'),
            'unit': 'м',
            'stock': 500,
            'brand': 'Камкабель',
            'description': 'Кабель силовой медный, негорючий. Сечение: 3x2.5мм². Для внутренней проводки.',
            'material': 'Медь, ПВХ',
            'weight': Decimal('0.15')
        },

        # САНТЕХНИКА
        {
            'category': plumbing,
            'name': 'Смеситель для кухни',
            'slug': 'kitchen-faucet',
            'price': Decimal('2899.99'),
            'unit': 'шт',
            'stock': 22,
            'brand': 'GROHE',
            'description': 'Смеситель для кухни с высоким изливом. Поворотный, керамический картридж.',
            'material': 'Латунь, хром',
            'color': 'Хром'
        },
        {
            'category': plumbing,
            'name': 'Труба ППР 20мм',
            'slug': 'ppr-pipe-20mm',
            'price': Decimal('159.99'),
            'unit': 'м',
            'stock': 300,
            'brand': 'PRO AQUA',
            'description': 'Труба полипропиленовая для водоснабжения. Диаметр: 20мм. Давление: 20 атм.',
            'material': 'Полипропилен',
            'color': 'Белый'
        },
        {
            'category': plumbing,
            'name': 'Унитаз компакт',
            'slug': 'toilet-compact',
            'price': Decimal('8999.99'),
            'unit': 'шт',
            'stock': 7,
            'brand': 'SANITA',
            'description': 'Унитаз компакт с косым выпуском. Керамика, бачок в комплекте.',
            'material': 'Фаянс',
            'color': 'Белый'
        },

        # ОТДЕЛОЧНЫЕ МАТЕРИАЛЫ
        {
            'category': finishing,
            'name': 'Обои виниловые',
            'slug': 'vinyl-wallpaper',
            'price': Decimal('799.99'),
            'unit': 'рул',
            'stock': 42,
            'brand': 'ERISMANN',
            'description': 'Обои виниловые, моющиеся. Ширина: 53см, длина: 10м. Дизайн: под покраску.',
            'material': 'Винил, бумага',
            'color': 'Белый'
        },
        {
            'category': finishing,
            'name': 'Плитка керамическая 30x30см',
            'slug': 'ceramic-tile-30x30',
            'price': Decimal('899.99'),
            'unit': 'м²',
            'stock': 85,
            'brand': 'KERAMA MARAZZI',
            'description': 'Плитка керамическая для пола. Размер: 30x30см. Водопоглощение: <3%.',
            'material': 'Керамика',
            'color': 'Бежевый'
        },

        # ЛАКОКРАСОЧНЫЕ МАТЕРИАЛЫ
        {
            'category': paint,
            'name': 'Краска акриловая белая',
            'slug': 'acrylic-paint-white',
            'price': Decimal('1899.99'),
            'unit': 'л',
            'stock': 35,
            'brand': 'TIKKURILA',
            'description': 'Краска акриловая для стен и потолков. Матовая, моющаяся. Расход: 10м²/л.',
            'material': 'Акрил',
            'color': 'Белый',
            'weight': Decimal('1.4')
        },
        {
            'category': paint,
            'name': 'Лак паркетный матовый',
            'slug': 'parquet-varnish-matt',
            'price': Decimal('2499.99'),
            'unit': 'л',
            'stock': 28,
            'brand': 'LAKRA',
            'description': 'Лак для паркета и деревянных полов. Износостойкий, матовый.',
            'material': 'Полиуретан',
            'color': 'Прозрачный',
            'weight': Decimal('1.2')
        },

        # СТРОИТЕЛЬНЫЕ СМЕСИ
        {
            'category': building_mixes,
            'name': 'Цемент М500 50кг',
            'slug': 'cement-m500-50kg',
            'price': Decimal('599.99'),
            'unit': 'меш',
            'stock': 120,
            'brand': 'ЕВРОЦЕМЕНТ',
            'description': 'Цемент портландский М500 Д0. Вес: 50кг. Прочность: 500кгс/см².',
            'material': 'Цемент',
            'weight': Decimal('50')
        },
        {
            'category': building_mixes,
            'name': 'Штукатурка гипсовая 30кг',
            'slug': 'gypsum-plaster-30kg',
            'price': Decimal('489.99'),
            'unit': 'меш',
            'stock': 75,
            'brand': 'КНАУФ',
            'description': 'Штукатурка гипсовая для внутренних работ. Расход: 8.5кг/м² при слое 10мм.',
            'material': 'Гипс',
            'weight': Decimal('30')
        },

        # ИЗМЕРИТЕЛЬНЫЕ ИНСТРУМЕНТЫ
        {
            'category': measuring,
            'name': 'Лазерный уровень 360°',
            'slug': 'laser-level-360',
            'price': Decimal('3499.99'),
            'unit': 'шт',
            'stock': 18,
            'brand': 'BOSCH',
            'description': 'Лазерный нивелир с построением линий на 360°. Точность: ±0.2мм/м.',
            'material': 'Пластик, металл',
            'color': 'Зеленый',
            'weight': Decimal('0.9')
        },
        {
            'category': measuring,
            'name': 'Рулетка 5м',
            'slug': 'tape-measure-5m',
            'price': Decimal('349.99'),
            'unit': 'шт',
            'stock': 90,
            'brand': 'MATRIX',
            'description': 'Рулетка измерительная с автоматическим сматыванием. Длина: 5м, ширина ленты: 25мм.',
            'material': 'Пластик, сталь',
            'color': 'Желтый',
            'weight': Decimal('0.25')
        },

        # СРЕДСТВА ЗАЩИТЫ
        {
            'category': protection,
            'name': 'Перчатки строительные',
            'slug': 'construction-gloves',
            'price': Decimal('149.99'),
            'unit': 'пара',
            'stock': 200,
            'brand': 'FIT',
            'description': 'Перчатки строительные с ПВХ покрытием. Усиленные, износостойкие.',
            'material': 'Хлопок, ПВХ',
            'color': 'Синий'
        },
        {
            'category': protection,
            'name': 'Защитные очки',
            'slug': 'safety-glasses',
            'price': Decimal('299.99'),
            'unit': 'шт',
            'stock': 85,
            'brand': '3M',
            'description': 'Защитные очки прозрачные. Ударопрочные, боковая защита.',
            'material': 'Поликарбонат',
            'color': 'Прозрачный'
        },
    ]

    created_count = 0
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            slug=prod_data['slug'],
            defaults={
                'category': prod_data['category'],
                'name': prod_data['name'],
                'price': prod_data['price'],
                'unit': prod_data.get('unit', 'шт'),
                'stock': prod_data['stock'],
                'brand': prod_data.get('brand', ''),
                'description': prod_data['description'],
                'material': prod_data.get('material', ''),
                'weight': prod_data.get('weight'),
                'color': prod_data.get('color', ''),
                'dimensions': prod_data.get('dimensions', ''),
            }
        )
        if created:
            created_count += 1

    print(f"Создано {created_count} товаров")
    return Product.objects.all()


def main():
    """Основная функция"""
    print("Наполнение базы данных тестовыми данными...")
    print("-" * 50)

    # Создаем категории
    categories = create_categories()

    # Создаем товары
    products = create_products()

    print("-" * 50)
    print(f"ИТОГО:")
    print(f"Категорий: {categories.count()}")
    print(f"Товаров: {products.count()}")
    print("Наполнение базы данных завершено!")

    # Выводим примеры товаров по категориям
    print("\nПримеры товаров по категориям:")
    for category in categories:
        category_products = products.filter(category=category)[:3]
        print(f"\n{category.name}:")
        for product in category_products:
            print(f"  - {product.name} ({product.price} руб.)")


if __name__ == '__main__':
    main()