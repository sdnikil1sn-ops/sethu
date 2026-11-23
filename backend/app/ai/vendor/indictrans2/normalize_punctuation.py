# Vendored from AI4Bharat/IndicTrans2 @ 4f08e39cc6bf13cd62e2445dc725f22bff1a9219, inference/normalize_punctuation.py (MIT, see LICENSE).
# Changes: `regex` -> stdlib `re` (only standard syntax is used); unused imports (tqdm, sys) removed.
# IMPORTANT NOTE: DO NOT DIRECTLY EDIT THIS FILE
# This file was manually ported from `normalize-punctuation.perl`
# TODO: Only supports English, add others

import re
multispace_regex = re.compile("[ ]{2,}")
multidots_regex = re.compile(r"\.{2,}")
end_bracket_space_punc_regex = re.compile(r"\) ([\.!:?;,])")
digit_space_percent = re.compile(r"(\d) %")
double_quot_punc = re.compile(r"\"([,\.]+)")
digit_nbsp_digit = re.compile(r"(\d) (\d)")

def punc_norm(text, lang="en"):
    text = text.replace('\r', '') \
                .replace('(', " (") \
                .replace(')', ") ") \
                \
                .replace("( ", "(") \
                .replace(" )", ")") \
                \
                .replace(" :", ':') \
                .replace(" ;", ';') \
                .replace('`', "'") \
                \
                .replace('„', '"') \
                .replace('“', '"') \
                .replace('”', '"') \
                .replace('–', '-') \
                .replace('—', " - ") \
                .replace('´', "'") \
                .replace('‘', "'") \
                .replace('‚', "'") \
                .replace('’', "'") \
                .replace("''", "\"") \
                .replace("´´", '"') \
                .replace('…', "...") \
                .replace(" « ", " \"") \
                .replace("« ", '"') \
                .replace('«', '"') \
                .replace(" » ", "\" ") \
                .replace(" »", '"') \
                .replace('»', '"') \
                .replace(" %", '%') \
                .replace("nº ", "nº ") \
                .replace(" :", ':') \
                .replace(" ºC", " ºC") \
                .replace(" cm", " cm") \
                .replace(" ?", '?') \
                .replace(" !", '!') \
                .replace(" ;", ';') \
                .replace(", ", ", ") \
                
    
    text = multispace_regex.sub(' ', text)
    text = multidots_regex.sub('.', text)
    text = end_bracket_space_punc_regex.sub(r")\1", text)
    text = digit_space_percent.sub(r"\1%", text)
    text = double_quot_punc.sub(r'\1"', text) # English "quotation," followed by comma, style
    text = digit_nbsp_digit.sub(r"\1.\2", text) # What does it mean?
    return text.strip(' ')