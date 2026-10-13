
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

API = "https://api.alquran.cloud/v1"
DATA_DIR = Path("quran_data")
DATA_DIR.mkdir(exist_ok=True)

FAVORITES_FILE = DATA_DIR / "favorites.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

TEXT_ARABIC = "quran-uthmani"
TEXT_ENGLISH = "en.sahih"

LANG = "en"

MESSAGES = {
    "en": {
        "title": "QURAN READER",
        "menu": [
            "1. List all Surahs",
            "2. Read a Surah",
            "3. Search Surahs",
            "4. Go to an Ayah",
            "5. Favorites",
            "6. Last reading position",
            "7. Change language",
            "0. Exit",
        ],
        "choice": "Choose an option: ",
        "surah": "Enter Surah number (1-114): ",
        "ayah": "Enter Ayah number: ",
        "invalid": "Invalid input. Try again.",
        "loading": "Loading Quran data...",
        "error": "Could not download data. Check your internet connection.",
        "saved": "Saved to favorites.",
        "removed": "Removed from favorites.",
        "empty": "No favorites yet.",
        "search": "Enter Surah name or number: ",
        "not_found": "No Surah found.",
        "language": "Choose language: 1. English  2. Arabic: ",
        "saved_progress": "Reading position saved.",
        "exit": "May your reading be beneficial. Goodbye!",
        "press": "Press Enter to continue...",
        "no_progress": "No saved reading position.",
        "menu_error": "Please choose a valid menu option.",
    },
    "ar": {
        "title": "قارئ القرآن",
        "menu": [
            "1. عرض جميع السور",
            "2. قراءة سورة",
            "3. البحث عن سورة",
            "4. الانتقال إلى آية",
            "5. المفضلة",
            "6. آخر موضع للقراءة",
            "7. تغيير اللغة",
            "0. خروج",
        ],
        "choice": "اختر خيارًا: ",
        "surah": "أدخل رقم السورة (1-114): ",
        "ayah": "أدخل رقم الآية: ",
        "invalid": "إدخال غير صالح. حاول مرة أخرى.",
        "loading": "جارٍ تحميل بيانات القرآن...",
        "error": "تعذر تحميل البيانات. تحقق من اتصال الإنترنت.",
        "saved": "تمت الإضافة إلى المفضلة.",
        "removed": "تمت الإزالة من المفضلة.",
        "empty": "لا توجد آيات في المفضلة.",
        "search": "أدخل اسم السورة أو رقمها: ",
        "not_found": "لم يتم العثور على السورة.",
        "language": "اختر اللغة: 1. الإنجليزية  2. العربية: ",
        "saved_progress": "تم حفظ موضع القراءة.",
        "exit": "نسأل الله أن ينفعك بالقراءة. مع السلامة!",
        "press": "اضغط Enter للمتابعة...",
        "no_progress": "لا يوجد موضع قراءة محفوظ.",
        "menu_error": "يرجى اختيار خيار صحيح.",
    },
}


def t(key):
    return MESSAGES[LANG][key]


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def api_get(endpoint):
    url = f"{API}/{endpoint}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "QuranReaderPython/1.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))

    if result.get("code") != 200:
        raise ValueError("API returned an error")

    return result["data"]


def get_surahs():
    cache = DATA_DIR / "surahs.json"

    if cache.exists():
        data = read_json(cache, [])
        if data:
            return data

    print(t("loading"))
    data = api_get("surah")
    write_json(cache, data)
    return data


def get_surah(number):
    cache = DATA_DIR / f"surah_{number}.json"

    if cache.exists():
        data = read_json(cache, None)
        if data:
            return data

    print(t("loading"))
    data = api_get(
        f"surah/{number}/editions/{TEXT_ARABIC},{TEXT_ENGLISH}"
    )

    if len(data) != 2:
        raise ValueError("Unexpected API response")

    write_json(cache, data)
    return data


def show_surahs(surahs):
    print("\n" + "=" * 55)
    print(t("title"))
    print("=" * 55)

    for surah in surahs:
        print(
            f"{surah['number']:3}. "
            f"{surah['englishName']:<25} "
            f"{surah['name']} "
            f"({surah['numberOfAyahs']})"
        )


def display_ayah(surah_number, ayah_number):
    editions = get_surah(surah_number)
    arabic_data, english_data = editions

    if not 1 <= ayah_number <= len(arabic_data["ayahs"]):
        print(t("invalid"))
        return

    arabic = arabic_data["ayahs"][ayah_number - 1]["text"]
    english = english_data["ayahs"][ayah_number - 1]["text"]

    print("\n" + "-" * 60)
    print(
        f"{arabic_data['englishName']} "
        f"({arabic_data['name']})"
    )
    print(f"Ayah {ayah_number}")
    print()
    print(arabic)
    print()
    print(english)
    print("-" * 60)


def read_surah(surah_number):
    editions = get_surah(surah_number)
    arabic_data, english_data = editions

    print(f"\n{arabic_data['englishName']} - {arabic_data['name']}")
    print(
        f"Ayahs: {arabic_data['numberOfAyahs']} | "
        f"{arabic_data['revelationType']}"
    )

    favorites = read_json(FAVORITES_FILE, [])
    progress = {
        "surah": surah_number,
        "ayah": 1
    }

    for index, ayah in enumerate(arabic_data["ayahs"]):
        number = ayah["numberInSurah"]
        english = english_data["ayahs"][index]["text"]

        print(f"\n[{number}] {ayah['text']}")
        print(english)

        progress["ayah"] = number
        write_json(PROGRESS_FILE, progress)

        command = input(
            "\n[N] Next  [F] Favorite  [Q] Quit: "
        ).strip().lower()

        if command == "f":
            item = f"{surah_number}:{number}"

            if item not in favorites:
                favorites.append(item)
                write_json(FAVORITES_FILE, favorites)
                print(t("saved"))
            else:
                print("Already in favorites.")

        elif command == "q":
            return


def search_surahs(surahs):
    query = input(t("search")).strip().lower()

    matches = [
        s for s in surahs
        if query == str(s["number"])
        or query in s["englishName"].lower()
        or query in s["name"]
        or query in s["englishNameTranslation"].lower()
    ]

    if matches:
        show_surahs(matches)
    else:
        print(t("not_found"))


def go_to_ayah(surahs):
    try:
        surah_number = int(input(t("surah")))
        if not 1 <= surah_number <= 114:
            raise ValueError

        editions = get_surah(surah_number)
        max_ayah = len(editions[0]["ayahs"])

        ayah_number = int(input(t("ayah")))
        if not 1 <= ayah_number <= max_ayah:
            raise ValueError

        display_ayah(surah_number, ayah_number)

        write_json(
            PROGRESS_FILE,
            {"surah": surah_number, "ayah": ayah_number}
        )

    except ValueError:
        print(t("invalid"))


def show_favorites():
    favorites = read_json(FAVORITES_FILE, [])

    if not favorites:
        print(t("empty"))
        return

    for item in favorites:
        print(item)

    choice = input(
        "Enter Surah:Ayah to open, or Enter to return: "
    ).strip()

    if not choice:
        return

    try:
        surah_number, ayah_number = map(int, choice.split(":"))
        display_ayah(surah_number, ayah_number)

        remove = input(
            "Remove from favorites? (y/n): "
        ).strip().lower()

        if remove == "y" and choice in favorites:
            favorites.remove(choice)
            write_json(FAVORITES_FILE, favorites)
            print(t("removed"))

    except (ValueError, IndexError):
        print(t("invalid"))


def show_progress():
    progress = read_json(PROGRESS_FILE, None)

    if not progress:
        print(t("no_progress"))
        return

    display_ayah(progress["surah"], progress["ayah"])


def change_language():
    global LANG

    choice = input(t("language")).strip()

    if choice == "1":
        LANG = "en"
    elif choice == "2":
        LANG = "ar"
    else:
        print(t("invalid"))


def main():
    global LANG

    while True:
        print("\n" + "=" * 40)
        print(t("title"))
        print("=" * 40)

        for item in t("menu"):
            print(item)

        choice = input("\n" + t("choice")).strip()

        try:
            if choice == "1":
                show_surahs(get_surahs())

            elif choice == "2":
                number = int(input(t("surah")))
                if not 1 <= number <= 114:
                    print(t("invalid"))
                else:
                    read_surah(number)

            elif choice == "3":
                search_surahs(get_surahs())

            elif choice == "4":
                go_to_ayah(get_surahs())

            elif choice == "5":
                show_favorites()

            elif choice == "6":
                show_progress()

            elif choice == "7":
                change_language()

            elif choice == "0":
                print(t("exit"))
                break

            else:
                print(t("menu_error"))

        except (urllib.error.URLError, TimeoutError, OSError,
                ValueError, KeyError, IndexError) as error:
            print(t("error"))
            # Uncomment for debugging:
            # print(error)

        input("\n" + t("press"))


if __name__ == "__main__":
    main()
