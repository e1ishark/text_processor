from collections import defaultdict
import re
import pymorphy3
import inspect
from text_mode import Mode

class TextProcessor:
    
    prefix1 = ['из', 'воз', 'вз', 'воз', 'раз', 'роз', 'низ']
    prefix2 = ['без', 'через', 'чрез']
    voiceless_consonants = ['к', 'п', 'с', 'т', 'ф', 'х', 'ч', 'ц', 'ш', 'щ']
    hissing_sounds = ['ж', 'ш', 'щ', 'ч']
    
    # Функция, которая разбивает строку на слова и убирает всю пунктуацию.
    def split_words(self, text):
        words = re.findall(r'\w+', text)  # находим все слова в тексте, используя регулярное выражение \w+
        # убираем всю пунктуацию из слов, используя метод split() с регулярным выражением \W+
        words = [word for word in re.split(r'\W+', ' '.join(words)) if word]
        return words


    # Функция для проверки, начинается ли данное слово с заданной приставки.
    def is_prefix(self, prefix, word):
        if word.startswith(prefix):
            return True
        else:
            return False
        
    # Функция для проверки, заканчивается ли данное слово на заданное окончание.
    def is_ending(self, ending, word):
        if word.endswith(ending):
            return True
        else:
            return False

    # Функция для поиска замены в словах с приставками -из, -воз/вз, -раз/роз, -низ, -без, - через/чрез
    def prefix_check(self, words):
        
        prefix1 = self.prefix1
        prefix2 = self.prefix2
        voiceless_consonants = self.voiceless_consonants
        key_words = defaultdict(list)
        
        for i in range(len(words)):
            for j in range(len(prefix1)):
                if self.is_prefix(prefix1[j], words[i]) == True:
                    word = words[i]
                    if word[len(prefix1[j])] == 'с':
                        position = len(prefix1[j]) - 1
                        word = word[:position] + 'с' + word[position+1:]
                        key_words[word].append(words[i])
                # print("w:", words[i], ", pre:", prefix1[j], ", isprefix:", text_processor.is_prefix(prefix1[j], words[i]))
            for k in range(len(prefix2)):
                if self.is_prefix(prefix2[k], words[i]) == True:
                    word = words[i]
                    for m in range(len(voiceless_consonants)):
                        if word[len(prefix2[k])] == voiceless_consonants[m]:
                            position = len(prefix2[k]) - 1
                            word = word[:position] + 'с' + word[position+1:]
                            key_words[word].append(words[i])
                            
        return key_words
    
    # Функция для поиска замены в словах сущ., III скл., т.п.
    def noun_thirdDeclension_instrumental_check(self, words):
        
        ending1 = 'ію'
        key_words = defaultdict(list)
        morph_analyzer = pymorphy3.MorphAnalyzer()
        
        for i in range(len(words)):
            if self.is_ending(ending1, words[i]):
                word = words[i]
                stem = word[:-len(ending1)]
                word = stem + 'ью'
                parsed_word = morph_analyzer.parse(word)[0]

                lemma = ''
                lemmas = set()
                for p in morph_analyzer.parse(word):
                    lemmas.add(p.normal_form)

                for l in lemmas:
                    p = morph_analyzer.parse(l)[0]
                    if morph_analyzer.word_is_known(l):
                        lemma = l
                    else:
                        continue
                parsed_word = morph_analyzer.parse(lemma)[0]
                # Проверка:
                # падеж - творительный
                # склонение - третье
                
                if 'NOUN' in parsed_word.tag and 'gent' in parsed_word.tag:
                    continue
                else:
                    key_words[word].append(words[i])
                    
        return key_words
    
    # Функция для поиска замены в словах прил., мн.ч., ж.р./ср.р.
    def plural_adj_neuterOrFem_check(self, words):
        
        ending1 = 'ыя'
        ending2 = 'ія'
        key_words = defaultdict(list)
        morph_analyzer = pymorphy3.MorphAnalyzer()
        
        for i in range(len(words)):
            if self.is_ending(ending1, words[i]):
                word = words[i]
                print(word, words[i])
                word = word[:-len(ending1)] + 'ые'
            elif self.is_ending(ending2, words[i]):
                word = words[i]
                word = word[:-len(ending2)] + 'ие'
            else:
                continue
            
            parsed_word = morph_analyzer.parse(word)[0]
            
            if parsed_word.tag.POS == "ADJF" and parsed_word.tag.number == "plur":
                lemma = parsed_word.normalized.word
                # проверяем, что лемма - мужской род, единственное число, именительный падеж
                lemma_parse = morph_analyzer.parse(lemma)[0]

                if lemma_parse.tag.gender == 'masc' and lemma_parse.tag.number == 'sing' and lemma_parse.tag.case == 'nomn':
                    # сохраняем замену окончания
                    key_words[word].append(words[i])
        
        return key_words
    
    # Функция для поиска замены в словах сущ., ср.р., II скл., п.п.
    # (оканчивающиеся на -ье)
    def noun_secondDeclension_neuter_prepositional_check(self, words, mode):
        
        ending1 = 'ьи'
        key_words = defaultdict(list)
        morph_analyzer = pymorphy3.MorphAnalyzer()
        
        for i in range(len(words)):
            if self.is_ending(ending1, words[i]):
                word = words[i]
                word = word[:-len(ending1)] + 'ье'
                if mode == Mode.NORMAL:
                    key_words[word].append(words[i])
                    
                elif mode == Mode.POETIC:
                    parsed_word = morph_analyzer.parse(word)[0]
                    lemma = parsed_word.normal_form
                    if lemma.endswith('ье'):
                        key_words[word].append(words[i])
                    
        return key_words
    
    # Функция для поиска замены в словах прил./мест./прич./числ., р.п./в.п.,
    # м.р./ср.р. (оканчивающиеся на -ый, -ій).
    def adj_pronoun_adverb_numeral_check(self, words):
        
        ending1 = 'аго'
        ending2 = 'яго'
        key_words = defaultdict(list)
        morph_analyzer = pymorphy3.MorphAnalyzer()
        hissing_sounds = self.hissing_sounds
        
        for i in range(len(words)):
            if self.is_ending(ending1, words[i]) or self.is_ending(ending2, words[i]):
                word = words[i]
                
                if morph_analyzer.word_is_known(word):
                    continue
                else:
                    if self.is_ending(ending1, word):
                        
                        for j in range(len(hissing_sounds)):
                            if word[len(word)-len(ending1)-1] == hissing_sounds[j]:
                                word = word[:-len(ending1)] + 'его'
                                
                                key_words[word].append(words[i])
                                break;
                            word = word[:-len(ending1)] + 'ого'
                            
                            key_words[word].append(words[i])
                            
                    elif self.is_ending(ending2, word):
                        word = word[:-len(ending2)] + 'его'
                        
                        parse = morph_analyzer.parse(word)[0]
                        
                        if parse.tag.POS in ["ADJF", "NPRO", "PRTF", "NUMR"] and \
                        parse.tag.case in ["accs", "gent"] and \
                        parse.tag.gender in ["masc", "neut"] and \
                        word.endswith(("ый", "ій", "ий")):
                            
                            lemma = parse.normal_form
                            parse_lemma = morph.parse(lemma)[0]
                            
                            if parse_lemma.normal_form == lemma and \
                            parse_lemma.tag.POS == parse.tag.POS:
                                
                                key_words[word].append(words[i])
                            else:
                                continue
                        else:
                            continue
                            
        return key_words
    
    # Функция для замены в тексте букв из древнерусского алфавита буквами современного алфавита
    def replace_letters(self, text):
        old_letters = {
            'ѣ': 'е',
            'i': 'и',
            'ѳ': 'ф',
            'ѵ': 'и',
            'ѕ': 'з',
            'ѯ': 'кс',
            'ѱ': 'пс',
            'і': 'и'
        }
        
        # for old_letter, new_letter in old_letters.items():
        #     text = re.sub(old_letter, new_letter, text)
        
        # Регулярное выражение для поиска букв дореформенного русского алфавита
        regex = re.compile("|".join(map(re.escape, old_letters.keys())))
        
        # Замена символов
        text = regex.sub(lambda match: old_letters[match.group(0)], text)
        return text


    def check_and_remove_hard_sign(self, words):
        
        morph = pymorphy3.MorphAnalyzer()
        key_words = defaultdict(list)

        for word in words:
            parsed_word = morph.parse(word)[0]

            if parsed_word.is_known == False and (word.endswith('ъ') or (word.endswith('ь'))):
                new_word = word[:-1]
                key_words[new_word].append(word)

        return key_words