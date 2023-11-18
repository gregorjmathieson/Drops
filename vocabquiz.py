# main.py
import discord
import pandas as pd
import re

from deep_translator import GoogleTranslator


intents = discord.Intents.all()
client = discord.Client(command_prefix="!", intents=intents)

langs = {
    'english': 'ENG',
    'arabic' : "AR",
    'danish' : "DA",
    'german' : "DE",
    'greek' : "EL",
    'esperanto' : "EO",
    'spanish' : "ES",
    'mexican spanish' : "ESMX",
    'farsi' : "FA",
    'finnish' : "FI",
    'french' : "FR",
    'hawaiian' : "HAW",
    'hebrew' : "HE",
    'hindi' : "HI",
    'hungarian' : "HU",
    'icelandic' : "IC",
    'indonesian' : "ID",
    'bahasa indonesia' : "ID",
    'italian' : "IT",
    'japanese' : "JP",
    'korean' : "KO",
    'maori' : "MI",
    'dutch' : "NL",
    'norwegian' : "NO",
    'polish' : "PL",
    'portuguese' : "PT",
    'russian' : "RU",
    'samoan' : "SM",
    'swedish' : "SV",
    'thai' : "TH",
    'tagalog' : "TL",
    'turkish' : "TR",
    'vietnamese' : "VI",
    'chinese' : "ZH",
    'cantonese' : "ZHYUE"
}

def get_file_contents(filename):
    """Takes text from given file using filename. Used for API key.

    Args:
        filename (str): Name of file to be read.

    Returns:
        str: Returns text content of a file.
    """
    try:
        with open(filename, "r") as f:
            #Get api key from apikey file.
            return f.read().strip()
    except FileNotFoundError:
        print(f"'{filename}' file not found.")
        print("Do you have an apikey?")
        print("Follow this tutorial -> https://github.com/dylburger/reading-api-key-from-file/blob/master/Keeping%20API%20Keys%20Secret.ipynb")
        print("Ask Gregor for an API Key.")

TOKEN = get_file_contents("token")
openai.api_key = get_file_contents("apikey")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

def scoreboard_update(user_id, language):
    score_df = pd.read_csv("./Drops/scoreboard.csv")
    print(language)
    if user_id in score_df["ID"].values:
        score_df.loc[score_df["ID"] == user_id, language] += 1
    else:
        # User does not exist, add a new row
        new_row = [len(score_df), str(user_id)] + [0] * len(langs)
        score_df.loc[len(score_df)] = new_row
        # Increment the language score for the new user
        score_df.loc[score_df["ID"] == str(user_id), language] += 1
    score_df.to_csv("./Drops/scoreboard.csv",index=False)

def translate_to_eng(text):
    translator = GoogleTranslator(target="en")
    return translator.translate(text, return_all=True)

ACTIVE_WORDS = {}
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if '!vocab' in str.lower(message.content):
        msg = str.lower(message.content)
        lang = msg[7:].strip()
        try:
            key = langs[lang]
        except KeyError:
            response = f"Sorry! Language **{lang}** not supported"
            await message.channel.send(response)
            return
        #DIFFERENT FOR ENGLISH
        if lang == "english":
            vocab_df = pd.read_csv(f"./Drops/drops_{key}_to_ENG.csv",names=["Word"])
            sample = vocab_df.sample(n=1)
            word = list(sample["Word"])[0]
            descr = f"# {word}\n."
            response = discord.Embed(title=f"VOCAB QUIZ\nLANGUAGE: {lang.upper()}",description=descr)
            await message.channel.send(embed=response)
            ACTIVE_WORDS[word] = (word, lang)
            return
        #Normal for everything else
        vocab_df = pd.read_csv(f"./Drops/drops_{key}_to_ENG.csv",names=["Word","Definition","Category","Subcategory","ID"])
        print(vocab_df)
        # descr = f"# {kanji}\n\n**Reading:** ||{reading}||"
        sample = vocab_df.sample(n=1)
        word = list(sample["Word"])[0]
        definition = list(sample["Definition"])[0]
        category = list(sample["Category"])[0]
        subcategory = list(sample["Subcategory"])[0]
        ID = sample["ID"]
        print(word)
        print(definition)
        descr = f"# {word}\nCategory: ||{category}||"
        response = discord.Embed(title=f"VOCAB QUIZ\nLANGUAGE: {lang.upper()}",description=descr)
        await message.channel.send(embed=response)
        ACTIVE_WORDS[word] = (definition, lang)

    if (message.reference is not None) and (len(ACTIVE_WORDS) != 0):
        answer = str.lower(message.content)
        print(message.content)
        check = await message.channel.fetch_message(message.reference.message_id)
        s = check.embeds[0].description
        result = re.search('# (.*)\n', s)
        word = result.group(1)
        test = ACTIVE_WORDS[word][0]
        if answer == "!reveal": #reveal the answer
            await message.reply(f"The answer is: {test}")
            ACTIVE_WORDS.pop(word)
            return
        # DIFFERENT IF ENGLISH
        if ACTIVE_WORDS[word][1] == "english":
            # translate into english first
            answer = translate_to_eng(answer)
            print(answer)
        # SAME FOR ALL ELSE
        if answer[0:4] == "the " and test[0:4] != "the ":
            answer = answer[4:] # gets rid of the word the
        test = re.sub(r'\W+', '', ACTIVE_WORDS[word][0].lower())
        answer = re.sub(r'\W+', '', answer.lower())
        print(answer.lower(), test)
        if answer == test:
            lang = ACTIVE_WORDS[word][1]
            ACTIVE_WORDS.pop(word)
            await message.reply("Correct!")
            author = message.author
            scoreboard_update(author.id, lang)
        else:
            await message.reply("Wrong!")

    if '!scoreboard' in str.lower(message.content):
        # create score dataframe
        score_df = pd.read_csv("./Drops/scoreboard.csv")
        subscore_df = pd.DataFrame()
        # read language
        msg = str.lower(message.content)
        lang = msg[12:].strip()
        if lang =="":
            sums_df = pd.DataFrame(score_df.loc[:, "arabic":].sum(axis=1), columns=['Sum'])
            sums_df['Best Language'] = score_df.loc[:, "arabic":].idxmax(axis=1)
            sums_df["ID"] = score_df["ID"]
            sums_df.sort_values(by='Sum', ascending=False, inplace=True)
            sums_df = sums_df.head(5)
            IDs = list(sums_df["ID"])
            scores = list(sums_df["Sum"])
            languages_ = list(sums_df["Best Language"])
            descr = ""
            for i, ID in enumerate(IDs):
                user_ = await client.fetch_user(ID)
                row_ = f"**{i+1}. {user_.display_name}**: {scores[i]} Points Overall, *Best Language: {languages_[i].title()}*\n"
                descr += row_
            response = discord.Embed(title="OVERALL SCOREBOARD",description=descr)
            await message.channel.send(embed=response)
            return
        try:
            key = langs[lang] # just to check if the language exists
        except KeyError:
            response = f"Sorry! Language **{lang}** not supported"
            await message.channel.send(response)
            return
        score_df = pd.read_csv("./Drops/scoreboard.csv")
        subscore_df = pd.DataFrame()
        subscore_df["ID"] = score_df["ID"]
        subscore_df["Score"]  = score_df[lang]
        subscore_df.sort_values(by='Score', ascending=False, inplace=True)
        subscore_df = subscore_df.head(5)
        IDs = list(subscore_df["ID"])
        scores = list(subscore_df["Score"])
        descr = ""
        for i, ID in enumerate(IDs):
            user_ = await client.fetch_user(ID)
            row_ = f"**{i+1}. {user_.display_name}**: {scores[i]} Points\n"
            descr += row_
        response = discord.Embed(title=f"{lang.upper()} SCOREBOARD",description=descr)
        await message.channel.send(embed=response)

client.run(TOKEN)