from flask import Flask, jsonify, render_template
from collections import Counter
import os
import re
import fulltext

app = Flask(__name__)
extension_file = None  # if the user wants a special extension
app.config['JSON_AS_ASCII'] = False  # correct display of Russian characters in some browsers


class WordInfo():
    """
    An object of this class will be created each time we access @app.route('/word=...')
    """

    ENGLISH_ALPHABET = set("abcdefghijklmnopqrstuvwxyz")
    RUSSIAN_ALPHABET = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    SYMBOLS = set("'-")
    VOWELS = set("aeiouаоиеёэыуюя")
    CONSONANTS = set("bcdfghjklmnpqrstvwxyzбвгджзйклмнпрстфхцчшщъь")

    def get_number_of_syllables_in_word(self, word):
        """
         This function will count the number of syllables in a word
        """

        syllableCount = 0
        # check the validity of the word
        word = word.lower()
        for letter in word:
            if letter not in self.ENGLISH_ALPHABET and letter not in self.RUSSIAN_ALPHABET and \
                    letter not in self.SYMBOLS:
                raise TypeError

        # determine in which language our word is
        flag_rus = False
        flag_en = False

        for letter in word:
            if letter in self.ENGLISH_ALPHABET and not flag_rus:
                flag_en = True
            elif letter in self.RUSSIAN_ALPHABET and not flag_en:
                flag_rus = True
            elif letter in self.SYMBOLS:
                pass
            # if the word consists of Russian and English words, then this is not a word, raise TypeError
            else:
                raise TypeError

        # Only one hyphen and one apostrophe is allowed
        if word.count('-') > 1 or word.count("'") > 1:
            raise TypeError

        # If the word contains a hyphen, then we divide it into two
        if ('-') in word:
            if not word.startswith('-') and not word.endswith('-'):
                first_part = word[:word.find('-')]
                second_part = word[word.find('-') + 1:]
                count_first_part = self.get_number_of_syllables_in_word(first_part)
                count_second_part = self.get_number_of_syllables_in_word(second_part)
                total_syllable_count = count_first_part + count_second_part
                return total_syllable_count
            else:
                raise TypeError

        # Some words may have contractions such as I've, Let's, Don't
        # They have no effect on the number of syllables, so we can drop them
        # exception: o'clock

        if "'" in word:
            if len(word) == 1:
                raise TypeError
            # 'em, 'cause
            if word.startswith("'"):
                word = word[1:]
            # didn't, don't
            elif word.endswith("n't"):
                word = word[:word.find("'")]
            # exception
            elif word == "o'clock":
                syllableCount = 2
                return syllableCount
            # I've Let's
            else:
                word = word[:word.find("'")]

        if flag_en:
            vowels = "aeiou"

            # Here are the rules for counting syllables:

            # Each group of adjacent vowels counts as one syllable
            flag = False  # make the truth, if the vowel, until the consonant is caught
            for index in range(len(word)):
                if word[index] in vowels and not flag:
                    syllableCount += 1
                    flag = True
                elif word[index] not in vowels:
                    flag = False

            # But if there is a suffix 'ing', which is preceded by a vowel, add one (queueing)
            if word.endswith('ing') and len(word) >= 4 and word[-4] in vowels:
                syllableCount += 1

            # The letter 'y' is a consonant that volunteers as a vowel when necessary
            # When there is a consonant before 'y' (python, many, sky)
            for index in range(1, len(word)):
                if word[index] == 'y' and word[index - 1] not in vowels:
                    syllableCount += 1

            # An ‘e’ or ‘ed’ at the end of a word does not count as a syllable (validate)
            # There are only few words where this rule eliminates actual syllables
            # 'ed' after 't' or 'd' is not silent (interested, divided)
            if word.endswith('e') or word.endswith('es'):
                syllableCount -= 1
                # If the rule 'vowel + consonant + silent e' is satisfied, then that's all
                if word.endswith('es') and len(word) >= 4 and word[-3] not in vowels and word[-4] in vowels:
                    pass
                elif word.endswith('e') and len(word) >= 3 and word[-2] not in vowels and word[-3] in vowels:
                    pass
                # If word end with 'se' it's always sylent (glimpse, prose, masse)
                elif word.endswith('se'):
                    pass
                # But if it has only one vowel or one set of consecutive vowels, then add 1 (cliche, seance)
                else:
                    if word.endswith('e'):
                        temp_word = word[:-1]
                    else:
                        temp_word = word[:-2]
                    temp_count = 0
                    flag = False  # make the truth, if the vowel, until the consonant is caught
                    for index in range(len(temp_word)):
                        if temp_word[index] in vowels and not flag:
                            temp_count += 1
                            flag = True
                        elif temp_word[index] not in vowels:
                            flag = False
                    if temp_count == 1:
                        syllableCount += 1

            if word.endswith('ed') and len(word) >= 3 and (word[-3] != 't' and word[-3] != 'd'):
                syllableCount -= 1

            # Words having double ‘e’ at the end do not lose a syllable for their count (comittee)
            if word.endswith('ee') or word.endswith('ees'):
                # Are there any other vowels? (see) If no, do not add, because we took it into account before

                temp_word = word[:-2] if word.endswith('ee') else word[:-3]

                for letter in temp_word:
                    if letter in vowels:
                        syllableCount += 1
                        break
            # Subtract 1 only if the letter before the 'le' at the end is vowel (scale, file)
            elif word.endswith('le') and len(word) >= 3 and word[-3] in vowels:
                syllableCount -= 1
            # If word ends with 'ly' after 'e', subtract one (safely, likely)
            elif word.endswith('ly') and len(word) >= 3 and word[-3] == 'e':
                syllableCount -= 1
            # If word ends with 'ian', should be counted as two syllables,
            # except 'tian' and 'cian' (radian, indian, politician , christian)
            elif word.endswith('ian') and not word.endswith('tian') and not word.endswith('cian'):
                syllableCount += 1

            # Each word has at least one syllable
            # Even if a word does not contain any vowel, or the previous rules give a count of zero,
            # it is still counted as having one syllable (str, she, he, fed, led)
            if syllableCount == 0 and len(word) != 0:
                syllableCount += 1

            return syllableCount

        if flag_rus:
            # The search for vowels in Russian satisfies the rule: number of syllables is equal to the number of vowels
            syllableCount = self.get_number_of_vowels(word)
            return syllableCount

    def get_number_of_consonants(self, word):
        """
        This function calculates the number of consonants in a word
        """
        word = word.lower()
        countConsonants = 0

        for letter in word:
            if letter in self.CONSONANTS:
                countConsonants += 1
        return countConsonants

    def get_number_of_vowels(self, word):
        """
        This function calculates the number of vowels in a word
        """
        word = word.lower()
        countVowels = 0

        for letter in word:
            if letter in self.VOWELS:
                countVowels += 1
        return countVowels


class FileInfo():
    """
    An object of this class will be created each time we access @app.route('/file=...')
    """

    def __init__(self, filename):
        """
        This function is responsible for the file extension and the correct splitting of the text into words.
        """
        if filename.endswith('.docx'):
            try:
                text = fulltext.get(filename).lower()
            # docx has some problems with empty files, catch them
            except:
                text = open(filename).read().lower()
        else:
            try:
                with open(filename) as f:
                    text = fulltext.get(f).lower()
            # for Russian
            except UnicodeDecodeError:
                with open(filename, encoding='WINDOWS-1251') as f:
                    text = fulltext.get(f).lower()
        # find all the words in English and Russian that have a hyphen or apostrophe
        words_with_extra_symbols = re.compile("[a-zа-я'-]+").findall(text)
        # sometimes an apostrophe and a hyphen remain from direct speech; we remove such elements
        self.words = [value for value in words_with_extra_symbols if
                      (value != "'" and value != "''" and value != "-")]  # direct speach

    def get_most_frequent_and_rarest_words(self, filename):
        """
        This function searches for the most frequent and rarest words in text files.
        """

        NUMBER_OF_WORDS_DISPLAYED = 3  # display three frequent and three rare words

        most_frequent_words = Counter(self.words).most_common(NUMBER_OF_WORDS_DISPLAYED)
        most_rarest_words = Counter(self.words).most_common()[-NUMBER_OF_WORDS_DISPLAYED:]
        dict_of_freq_words_and_occurrences = {}
        dict_of_rare_words_and_occurrences = {}
        for index in range(len(most_frequent_words)):
            dict_of_freq_words_and_occurrences[most_frequent_words[index][0]] = most_frequent_words[index][1]
            dict_of_rare_words_and_occurrences[most_rarest_words[index][0]] = most_rarest_words[index][1]

        dict_of_freq_and_rare_words = {}
        dict_of_freq_and_rare_words['MOST FREQUENT WORDS'] = dict_of_freq_words_and_occurrences
        dict_of_freq_and_rare_words['MOST RAREST WORDS'] = dict_of_rare_words_and_occurrences
        return dict_of_freq_and_rare_words

    def get_value_of_average_word_length(self):
        """
        This function calculates the average word length in text file
        """
        try:
            average = sum(len(word) for word in self.words) / len(self.words)
        # if the file is empty, then the average word length is zero
        except ZeroDivisionError:
            return 0
        average = round(average, 2)
        return average

    def get_syllable_to_words_ratio(self):
        """
        This function calculates the ratio of syllables to all words.
        """
        count_syllables = 0
        for word in self.words:
            try:
                count_syllables += WordInfo().get_number_of_syllables_in_word(word)
            except TypeError:
                pass
        try:
            ratio = count_syllables / len(self.words)
        # if the file empty, ratio is zero
        except ZeroDivisionError:
            return 0
        ratio = round(ratio, 2)
        return ratio

    def get_number_of_vowels_and_consonants(self):
        """
        This function counts the number of vowels and consonants in a file.
        """
        numberVowels = 0
        numberConconants = 0

        for word in self.words:
            numberConconants += WordInfo().get_number_of_consonants(word)
            numberVowels += WordInfo().get_number_of_vowels(word)
        dict_of_number_vowels_and_consonants = {}
        dict_of_number_vowels_and_consonants['NUMBER OF VOWELS'] = numberVowels
        dict_of_number_vowels_and_consonants['NUMBER OF CONSONANTS'] = numberConconants
        return dict_of_number_vowels_and_consonants


class FolderInfo():
    """
    An object of this class will be created each time we access @app.route('/')
    """

    def __init__(self):
        """
        Checking for the existence of a directory
        """
        SERVER_DEFAULT_DIRECTORY = './server files'
        if os.path.isdir(SERVER_DEFAULT_DIRECTORY):
            self.SERVER_DEFAULT_DIRECTORY = SERVER_DEFAULT_DIRECTORY
        else:
            raise FileExistsError

    def get_list_of_files(self, extension=None):
        """
        This function displays all files in the default folder of the server.
        """

        files = {}
        index = 0
        for dirname, dirnames, filenames in os.walk(self.SERVER_DEFAULT_DIRECTORY):
            # print path to all filenames
            for filename in filenames:
                name = os.path.join(dirname, filename)
                # if the user specified the desired file extension when displaying
                if extension:
                    if name.endswith('.' + extension):
                        files[index] = name
                        index += 1
                else:
                    files[index] = name
                    index += 1
        return files

    def get_list_of_subfolders(self):
        """
        This function displays all directories in the default folder of the server.
        """
        directories = []
        for dirname, dirnames, filenames in os.walk(self.SERVER_DEFAULT_DIRECTORY):
            # print path to all subdirectories
            for subdirname in dirnames:
                directories.append(os.path.join(dirname, subdirname))
        return directories


@app.errorhandler(404)
def page_not_found(e):
    """
    This function catches failed requests
    """
    return render_template('page_not_found.html')


@app.route('/', methods=['GET'])
@app.route('/ext=<string:ext>', methods=['GET'])
def folder_info(ext=None):
    """
    This function responds to the request and displays a list of folders and files.
    """
    global extension_file
    # if user specified extension, all functions should be aware of this
    if ext:
        extension_file = ext

    else:
        extension_file = None
    try:
        folder_info = FolderInfo()
    except:
        return render_template('folder_not_exists.html')
    list_of_subfolders = folder_info.get_list_of_subfolders()
    list_of_files = folder_info.get_list_of_files(ext)

    dict_folder_info = {'Directories': list_of_subfolders,
                        'Files': list_of_files,
                        'Number of files': len(list_of_files)}

    return jsonify({'Folder Info': dict_folder_info})


@app.route('/file=<int:index>', methods=['GET'])
def file_info(index):
    global extension_file
    supported_file_extensions = ['.txt', 'docx', '.html']
    # if the extension is set, then we work with the dictionary of files of this extension
    if extension_file:
        list_of_files = FolderInfo().get_list_of_files(extension_file)
    # if not, then we work with all files
    else:
        list_of_files = FolderInfo().get_list_of_files()
    # does the file exist under such key...
    try:
        file = list_of_files[index]
    except KeyError:
        return render_template('index_error_file.html')
    # does the file support any of the valid extensions...
    if not file.endswith(tuple(supported_file_extensions)):
        return render_template('extension_error_file.html')
    try:
        file_info = FileInfo(file)
    except:
        return render_template('wrong_content_in_file.html')
    dict_of_most_frequent_and_rarest_words = file_info.get_most_frequent_and_rarest_words(file)
    value_of_average_word_length = file_info.get_value_of_average_word_length()
    syllable_to_words_ratio = file_info.get_syllable_to_words_ratio()
    ratio_of_vowels_to_consonants = file_info.get_number_of_vowels_and_consonants()

    dict_file_info = {'Frequent and rare words in file': dict_of_most_frequent_and_rarest_words,
                      'Average length of words in file': value_of_average_word_length,
                      'Ratio of syllables to words': syllable_to_words_ratio,
                      'Number of vowels and consonants': ratio_of_vowels_to_consonants}

    return jsonify({'File Info about ' + file: dict_file_info})


@app.route('/word=<string:word>', methods=['GET'])
def word_info(word):
    word_info = WordInfo()
    dict_word_info = {}
    try:
        number_of_syllables = word_info.get_number_of_syllables_in_word(word)
    except TypeError:
        return render_template('bad_word.html')
    number_of_vowels = word_info.get_number_of_vowels(word)
    number_of_consonants = word_info.get_number_of_consonants(word)
    dict_word_info[word] = "SYLLABLES COUNT: " + str(number_of_syllables) + "; " + \
                           "VOWELS COUNT: " + str(number_of_vowels) + "; " + \
                           "CONSONANTS COUNT: " + str(number_of_consonants)
    return jsonify({'Word Info': dict_word_info})


if __name__ == '__main__':
    app.run(debug=True)
