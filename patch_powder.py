import os
import shutil
import struct
import sys


DEFAULT_GAME_DIR = r'C:\Program Files (x86)\Steam\steamapps\common\Powder'


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME_DIR

    if not os.path.isdir(game_dir):
        print(f"[Ошибка] Папка игры не найдена: {game_dir}")
        print("Укажите путь к папке игры аргументом: py patch_powder.py \"D:\\Games\\Powder\"")
        sys.exit(1)

    dest_exe = os.path.join(game_dir, 'Powder.exe')
    orig_exe = os.path.join(game_dir, 'Powder.exe.orig')

    if not os.path.exists(orig_exe):
        if not os.path.exists(dest_exe):
            print(f"[Ошибка] Файл Powder.exe не найден в {game_dir}")
            sys.exit(1)
        shutil.copy2(dest_exe, orig_exe)
        print(f"[OK] Создан бэкап оригинала: {orig_exe}")

    with open(orig_exe, 'rb') as f:
        data = bytearray(f.read())

    # =========================================================================
    # 1. NATIVE CP1251 -> CYRILLIC HOOK IN FontReader::lookupChar
    # =========================================================================
    cave_file = 0x6a6dc0
    cave_rva = 0x1000 + 0x6a69c0  # 0x6a79c0

    hook_file = 0x14fdf0
    hook_rva = 0x1000 + (0x14fdf0 - 0x400)  # 0x1509f0

    cave = bytearray()
    cave += b'\xf7\xc1\x00\xff\xff\xff'  # test ecx, 0xffffff00
    cave += b'\x75\x23'                  # jnz done (+35)
    cave += b'\x80\xf9\xc0'              # cmp cl, 0xc0
    cave += b'\x72\x08'                  # jb check_yo (+8)
    cave += b'\x81\xc1\x50\x03\x00\x00'  # add ecx, 0x350
    cave += b'\xeb\x16'                  # jmp done (+22)
    cave += b'\x80\xf9\xa8'              # cmp cl, 0xa8 ('Ё')
    cave += b'\x75\x07'                  # jne check_yo2 (+7)
    cave += b'\xb9\x01\x04\x00\x00'      # mov ecx, 0x401
    cave += b'\xeb\x0a'                  # jmp done (+10)
    cave += b'\x80\xf9\xb8'              # cmp cl, 0xb8 ('ё')
    cave += b'\x75\x05'                  # jne done (+5)
    cave += b'\xb9\x51\x04\x00\x00'      # mov ecx, 0x451
    # Stolen prologue bytes from 0x14fdf0 (push r15..r12)
    cave += b'\x41\x57\x41\x56\x41\x55\x41\x54'

    ret_target_rva = hook_rva + 8
    disp_back = ret_target_rva - (cave_rva + len(cave) + 5)
    cave += b'\xe9' + struct.pack('<i', disp_back)

    assert len(cave) <= 64, f"Cave size {len(cave)} > 64!"
    data[cave_file : cave_file + len(cave)] = cave

    disp_to_cave = cave_rva - (hook_rva + 5)
    data[hook_file : hook_file + 8] = b'\xe9' + struct.pack('<i', disp_to_cave) + b'\x90\x90\x90'

    pe_offset = struct.unpack_from('<I', data, 0x3c)[0]
    opt_hdr_size = struct.unpack_from('<H', data, pe_offset + 20)[0]
    sec_table = pe_offset + 24 + opt_hdr_size
    new_vsize = 0x6a69c0 + len(cave)
    struct.pack_into('<I', data, sec_table + 8, new_vsize)
    print("[OK] Установлен нативный хук FontReader::lookupChar (CP1251 -> Unicode)")

    # =========================================================================
    # 2. PATCH CLASSIC _M_tolower TABLE FOR CP1251 RUSSIAN LOWERCASE
    # =========================================================================
    tbl_offset = 0x754a40
    for c in range(0xC0, 0xE0):
        data[tbl_offset + c] = c + 0x20
    data[tbl_offset + 0xA8] = 0xB8
    print("[OK] Пропатчена таблица _M_tolower для кириллицы")

    # =========================================================================
    # 3. STRING PATCHING HELPERS
    # =========================================================================
    def replace_fixed(orig_s, ru_s):
        orig_b = orig_s.encode('ascii')
        ru_b = ru_s.encode('cp1251')
        if len(ru_b) < len(orig_b):
            ru_b = ru_b + b' ' * (len(orig_b) - len(ru_b))
        elif len(ru_b) > len(orig_b):
            ru_b = ru_b[:len(orig_b)]
        count = 0
        pos = 0
        while True:
            pos = data.find(orig_b + b'\x00', pos)
            if pos == -1:
                break
            data[pos : pos + len(ru_b)] = ru_b
            count += 1
            pos += len(ru_b) + 1
        return count

    def replace_raw(orig_b, ru_s):
        ru_b = ru_s.encode('cp1251')
        if len(ru_b) < len(orig_b):
            ru_b = ru_b + b' ' * (len(orig_b) - len(ru_b))
        elif len(ru_b) > len(orig_b):
            ru_b = ru_b[:len(orig_b)]
        count = 0
        pos = 0
        while True:
            pos = data.find(orig_b, pos)
            if pos == -1:
                break
            data[pos : pos + len(ru_b)] = ru_b
            count += 1
            pos += len(ru_b)
        return count

    patched_total = 0

    # Wall descriptions
    fixed_pairs = [
        ('Erases walls.', 'Стирает стены'),
        ('Blocks everything. Conductive.', 'Блокирует всё. Проводит ток.  '),
        ('E-Wall. Becomes transparent when electricity is connected.', 'Э-Стена. Прозрачна при подаче напряжения на проводник.    '),
        ('Detector. Generates electricity when a particle is inside.', 'Детектор. Создает ток, когда внутри находится частица.    '),
        ('Streamline. Creates a line that follows air movement.', 'Линия тока. Отображает направление потоков воздуха.  '),
        ('Allows liquids, blocks all other particles. Conductive.', 'Пропускает жидкости, блокирует всё остальное. Проводник'),
        ('Absorbs particles but lets air currents through.', 'Поглощает частицы, но пропускает поток воздуха. '),
        ('Basic wall, blocks everything.', 'Базовая стена, держит всё.    '),
        ('Allows air, but blocks all particles.', 'Пропускает воздух, держит частицы.   '),
        ('Allows powders, blocks all other particles.', 'Пропускает порошки, блокирует всё остальное'),
        ('E-Hole. absorbs particles, releases them when powered.', 'Э-Дыра. Поглощает материю, выпускает при токе.        '),
        ('Allows gases, blocks all other particles.', 'Пропускает газы, блокирует всё остальное.'),
        ('Gravity wall. Newtonian Gravity has no effect inside a box drawn with this.', 'Грави-стена. Гравитация Ньютона не действует внутри контура этой стены.    '),
        ('Allows energy particles, blocks all other particles.', 'Пропускает энергочастицы, блокирует всё остальное.  '),
        ('Allows all particles, but blocks air.', 'Пропускает частицы, но держит воздух.'),
        ('Erases walls, particles, and signs.', 'Стирает стены, частицы и надписи.  '),
        ('Freezes particles inside the wall in place until powered.', 'Замораживает частицы внутри стены до подачи напряжения.  '),
        # Wall names
        ('CONDUCTIVE WALL', 'ПРОВОД СТЕНА   '),
        ('EWALL', 'ЭСТЕН'),
        ('DETECTOR', 'ДЕТЕКТОР'),
        ('STREAMLINE', 'ЛИНИЯ ТОКА'),
        ('LIQUID WALL', 'ЖИДК СТЕНА '),
        ('ABSORB WALL', 'ПОГЛ СТЕНА '),
        ('AIRONLY WALL', 'ВОЗД СТЕНА  '),
        ('POWDER WALL', 'СЫПУЧ СТЕНА'),
        ('CONDUCTOR', 'ПРОВОДНИК'),
        ('EHOLE', 'ЭДЫРА'),
        ('GAS WALL', 'ГАЗ СТЕНА'),
        ('GRAVITY WALL', 'ГРАВ СТЕНА  '),
        ('ENERGY WALL', 'ЭНЕРГ СТЕНА'),
        ('AIRBLOCK WALL', 'СТОП ВОЗДУХ  '),
        ('ERASEALL', 'ОЧИСТИТЬ'),
        ('STASIS WALL', 'СТАЗ СТЕНА '),
        # Search & Dialogs
        ('Element Search', 'Поиск элемента'),
        ('Are you sure you want to exit the game?', 'Вы уверены, что хотите выйти из игры?  '),
        ('You are about to quit', 'Вы выходите из игры  '),
        ('Fast quit', 'Быстр.вых'),
        ('Sticky categories', 'Фикс. категории  '),
        ('Include pressure', 'Включать давлен.'),
        ('Perfect circle brush', 'Круглая форма кисти '),
        ('Open data folder', 'Папка с данными '),
        # Bottom bar & tools
        ('[untitled simulation]', '[без названия]'),
        ('Vote', 'ОЦ'),
        ('[no tags set]', '[нет тегов]'),
        ('[sign in]', '[войти]'),
        ('Search for elements', 'Поиск элементов'),
        ('Erase everything', 'Очистить всё'),
        ('Reload the simulation', 'Перезагрузить'),
        # Categories
        ('Walls', 'Стены'),
        ('Electronics', 'Электроника'),
        ('Powered Materials', 'Проводники'),
        ('Sensors', 'Сенсоры'),
        ('Force', 'Силы'),
        ('Explosives', 'Взрывчатка'),
        ('Gases', 'Газы'),
        ('Liquids', 'Жидкости'),
        ('Powders', 'Сыпучие'),
        ('Solids', 'Твердые'),
        ('Radioactive', 'Радиоактив.'),
        ('Special', 'Особые'),
        ('Game Of Life', 'Игра Жизнь'),
        ('Tools', 'Орудия'),
        ('Favorites', 'Избранное'),
        ('Decoration tools', 'Декорации'),
        # HUD
        ('Empty, Pressure: ', 'Пусто, Давление: '),
        ('Empty', 'Пусто'),
    ]

    raw_pairs = [
        (b'Fan. Accelerates air. Use the line tool to set direction and str', 'Вентилятор. Разгоняет воздух. Тяните линию для направления.     '),
        (b'Conductor. Allows all particles to pass through and conducts elects electricity.', 'Проводник. Пропускает любые частицы и проводит электрический ток.               '),
        (b'Heat simulation \x08gIntroduced in version 34', 'Симуляция тепла \x08gДобавлена в версии 34'),
        (b'Newtonian gravity \x08gIntroduced in version 48', 'Гравитация Ньютона \x08gВерсия 48        '),
        (b'Ambient heat simulation \x08gIntroduced in version 50', 'Тепло окруж. среды \x08gДобавлено в v50       '),
        (b'Water equalisation \x08gIntroduced in version 61', 'Уравнивание воды \x08gДобавлено в v61    '),
        (b'Sand effect', 'Эффект песка'),
        (b'Draw gravity field \x08g(ctrl+g)', 'Сетка гравитации \x08g(ctrl+g)'),
        (b'Draw decorations \x08g(ctrl+b)', 'Слой декораций \x08g(ctrl+b)'),
        (b'Newtonian Gravity \x08g(n)', 'Гравит. Ньютона \x08g(n)'),
        (b'Ambient heat \x08g(u)', 'Тепло среды \x08g(u)'),
        (b'Show Console \x08g(~)', 'Консоль \x08g(~)'),
    ]

    for orig_s, ru_s in fixed_pairs:
        patched_total += replace_fixed(orig_s, ru_s)

    for orig_b, ru_s in raw_pairs:
        patched_total += replace_raw(orig_b, ru_s)

    with open(dest_exe, 'wb') as f:
        f.write(data)
    print(f"[OK] Powder.exe успешно пропатчен (заменено вхождений: {patched_total})")

    # =========================================================================
    # 4. COPY autorun.lua
    # =========================================================================
    src_lua = os.path.join(script_dir, 'autorun.lua')
    if os.path.exists(src_lua):
        shutil.copy2(src_lua, os.path.join(game_dir, 'autorun.lua'))
        userdata_dir = os.path.join(game_dir, 'userdata')
        if os.path.isdir(userdata_dir):
            shutil.copy2(src_lua, os.path.join(userdata_dir, 'autorun.lua'))
        print("[OK] Скопирован autorun.lua в папку игры и userdata/")
    else:
        print("[Предупреждение] autorun.lua не найден рядом со скриптом!")

    print("\nГотово! Русификатор (Late Alpha) успешно установлен.")


if __name__ == '__main__':
    main()
