from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json

load_dotenv()



class GenresWithinMood(BaseModel):
    name: str
    genres: list[str]

class Moods(BaseModel):
    moods: list[GenresWithinMood]

def mood_sorter(input):
    openai_key = os.environ.get("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_key)

    response = client.responses.parse(
        input = str(input),
        model="gpt-4.1",
        text_format=Moods,
        instructions="Sort given music genres to 4 different fitting moods (which you give a name to).",
        temperature=0.2,
    )

    mood_dict = json.loads(response.output_text)

    return mood_dict


"""
       {'alternative r&b', 'r&b', 'neo soul', 'retro soul', 'soul', 'quiet storm',
        'indie r&b', 'bedroom pop', 'singer-songwriter', 'bossa nova', 'jazz', 
        'indie jazz', 'jazz blues', 'swedish ballads', 'chamber pop', 'baroque pop',
        'nu jazz', 'jazz funk', 'latin jazz', 'brazilian jazz', 'motown', 'philly soul',
        'folk', 'folk rock', 'soft rock', 'house', 'jazz house', 'stutter house', 'french house', 'electro',
        'bass house', 'uk garage', 'techno', 'hypertechno', 'drum and bass',
        'liquid funk', 'electronic', 'bassline', 'italo disco', 'disco',
        'post-disco', 'boogie', 'funk', 'funk rock', 'jungle', 'rally house',
        'highlife', 'afrobeat', 'latin', 'latin jazz', 'brazilian jazz','hip hop', 'rap', 'alternative hip hop', 'cloud rap', 'rage rap',
        'melodic rap', 'emo rap', 'east coast hip hop', 'west coast hip hop', 
        'southern hip hop', 'latin hip hop', 'trap latino', 'reggaeton',
        'urbano latino', 'norwegian hip hop', 'jazz rap'}
"""